from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from threading import RLock

from .models import AnalysisResult, Candidate


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    analyzed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS candidates (
    id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL,
    shot_id TEXT NOT NULL,
    timestamp REAL NOT NULL,
    preview_path TEXT NOT NULL,
    categories_json TEXT NOT NULL,
    scores_json TEXT NOT NULL,
    embedding_ref TEXT,
    payload_json TEXT NOT NULL,
    FOREIGN KEY(video_id) REFERENCES videos(id)
);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT NOT NULL,
    video_id TEXT NOT NULL,
    shot_id TEXT NOT NULL,
    frame_id TEXT NOT NULL,
    timestamp REAL NOT NULL,
    categories_json TEXT NOT NULL,
    scores_json TEXT NOT NULL,
    embedding_ref TEXT,
    decision TEXT NOT NULL CHECK(decision IN ('KEEP','REJECT','FAVORITE','CLEAR')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(candidate_id) REFERENCES candidates(id)
);
CREATE TABLE IF NOT EXISTS preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    shot_id TEXT NOT NULL,
    candidate_a_id TEXT NOT NULL,
    candidate_b_id TEXT NOT NULL,
    winner_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_feedback_candidate ON feedback(candidate_id, created_at);
CREATE INDEX IF NOT EXISTS idx_candidates_video ON candidates(video_id, shot_id);
"""


class FeedbackStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=30)

    def save_analysis(self, result: AnalysisResult) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """INSERT INTO videos(id,path,metadata_json) VALUES(?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                    path=excluded.path,
                    metadata_json=excluded.metadata_json,
                    analyzed_at=CURRENT_TIMESTAMP""",
                (result.video.id, result.video.path, json.dumps(result.video.to_dict(), ensure_ascii=False)),
            )
            conn.executemany(
                """INSERT INTO candidates
                (id,video_id,shot_id,timestamp,preview_path,categories_json,scores_json,embedding_ref,payload_json)
                VALUES(?,?,?,?,?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET
                    video_id=excluded.video_id,
                    shot_id=excluded.shot_id,
                    timestamp=excluded.timestamp,
                    preview_path=excluded.preview_path,
                    categories_json=excluded.categories_json,
                    scores_json=excluded.scores_json,
                    embedding_ref=excluded.embedding_ref,
                    payload_json=excluded.payload_json""",
                [
                    (
                        item.id, item.video_id, item.shot_id, item.timestamp, item.preview_path,
                        json.dumps(item.labels), json.dumps(item.scores), item.hash64,
                        json.dumps(item.to_dict(), ensure_ascii=False),
                    )
                    for item in result.candidates
                ],
            )

    def record_feedback(self, candidate: Candidate, decision: str) -> None:
        if decision not in {"KEEP", "REJECT", "FAVORITE", "CLEAR"}:
            raise ValueError(f"Unknown feedback decision: {decision}")
        with self._lock, self._connect() as conn:
            conn.execute(
                """INSERT INTO feedback
                (candidate_id,video_id,shot_id,frame_id,timestamp,categories_json,scores_json,embedding_ref,decision)
                VALUES(?,?,?,?,?,?,?,?,?)""",
                (
                    candidate.id, candidate.video_id, candidate.shot_id, candidate.id, candidate.timestamp,
                    json.dumps(candidate.labels), json.dumps(candidate.scores), candidate.hash64, decision,
                ),
            )

    def latest_feedback(self) -> dict[str, str]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT f.candidate_id, f.decision FROM feedback f
                JOIN (SELECT candidate_id, MAX(id) AS max_id FROM feedback GROUP BY candidate_id) latest
                ON latest.max_id=f.id"""
            ).fetchall()
        return dict(rows)

    def record_preference(self, a: Candidate, b: Candidate, winner: Candidate) -> None:
        if a.video_id != b.video_id or a.shot_id != b.shot_id:
            raise ValueError("偏好对比的两张图片必须来自同一个镜头")
        if winner.id not in {a.id, b.id}:
            raise ValueError("胜出画面必须是 A 或 B")
        with self._lock, self._connect() as conn:
            conn.execute(
                """INSERT INTO preferences
                (video_id,shot_id,candidate_a_id,candidate_b_id,winner_id) VALUES(?,?,?,?,?)""",
                (a.video_id, a.shot_id, a.id, b.id, winner.id),
            )

    def preference_pairs(self) -> list[tuple[Candidate, Candidate]]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT winner.payload_json, loser.payload_json
                FROM preferences preference
                JOIN candidates winner ON winner.id = preference.winner_id
                JOIN candidates loser ON loser.id = CASE
                    WHEN preference.winner_id = preference.candidate_a_id THEN preference.candidate_b_id
                    ELSE preference.candidate_a_id
                END
                ORDER BY preference.id"""
            ).fetchall()
        return [
            (Candidate.from_dict(json.loads(winner)), Candidate.from_dict(json.loads(loser)))
            for winner, loser in rows
        ]

    def counts(self) -> dict[str, int]:
        with self._connect() as conn:
            return {
                "videos": conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0],
                "candidates": conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0],
                "feedback": conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0],
                "preferences": conn.execute("SELECT COUNT(*) FROM preferences").fetchone()[0],
            }
