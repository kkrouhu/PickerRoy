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

    def training_pairs(self, limit: int = 800) -> list[tuple[Candidate, Candidate]]:
        """Combine explicit A/B choices with the user's latest keep/favorite/reject decisions."""
        pairs: list[tuple[Candidate, Candidate]] = []
        seen: set[tuple[str, str]] = set()
        for winner, loser in self.preference_pairs():
            key = (winner.id, loser.id)
            if key not in seen:
                seen.add(key)
                pairs.append((winner, loser))
        with self._connect() as conn:
            feedback_rows = conn.execute(
                """SELECT candidate.payload_json, feedback.decision
                FROM feedback
                JOIN candidates candidate ON candidate.id=feedback.candidate_id
                JOIN (SELECT candidate_id, MAX(id) AS max_id FROM feedback GROUP BY candidate_id) latest
                  ON latest.max_id=feedback.id
                WHERE feedback.decision != 'CLEAR'
                ORDER BY feedback.id"""
            ).fetchall()
            candidate_rows = conn.execute("SELECT payload_json FROM candidates ORDER BY rowid").fetchall()

        decisions: dict[str, tuple[Candidate, str]] = {}
        for payload, decision in feedback_rows:
            candidate = Candidate.from_dict(json.loads(payload))
            decisions[candidate.id] = (candidate, decision)
        all_candidates = [Candidate.from_dict(json.loads(row[0])) for row in candidate_rows]

        by_video: dict[str, list[Candidate]] = {}
        for candidate in all_candidates:
            by_video.setdefault(candidate.video_id, []).append(candidate)
        def add(winner: Candidate, loser: Candidate) -> None:
            key = (winner.id, loser.id)
            if winner.id != loser.id and key not in seen and len(pairs) < limit:
                seen.add(key)
                pairs.append((winner, loser))

        for video_candidates in by_video.values():
            favorites = [item for item in video_candidates if decisions.get(item.id, (None, ""))[1] == "FAVORITE"]
            kept = [item for item in video_candidates if decisions.get(item.id, (None, ""))[1] == "KEEP"]
            rejected = [item for item in video_candidates if decisions.get(item.id, (None, ""))[1] == "REJECT"]
            neutral = [item for item in video_candidates if item.id not in decisions and not item.rejected]
            for winner in favorites:
                for loser in (rejected + kept)[:40]:
                    add(winner, loser)
                for loser in [item for item in neutral if item.shot_id == winner.shot_id][:6]:
                    add(winner, loser)
            for winner in kept:
                for loser in rejected[:40]:
                    add(winner, loser)
            for loser in rejected:
                for winner in [item for item in neutral if item.shot_id == loser.shot_id][:6]:
                    add(winner, loser)
        return pairs[:limit]

    def personalization_stats(self) -> dict[str, object]:
        latest = self.latest_feedback()
        counts = self.counts()
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT candidate.categories_json, feedback.decision
                FROM feedback
                JOIN candidates candidate ON candidate.id=feedback.candidate_id
                JOIN (SELECT candidate_id, MAX(id) AS max_id FROM feedback GROUP BY candidate_id) latest
                  ON latest.max_id=feedback.id
                WHERE feedback.decision != 'CLEAR'"""
            ).fetchall()
        decisions = {name: sum(1 for value in latest.values() if value == name)
                     for name in ("FAVORITE", "KEEP", "REJECT")}
        categories: dict[str, int] = {}
        for raw_categories, decision in rows:
            if decision not in {"FAVORITE", "KEEP"}:
                continue
            for category in json.loads(raw_categories):
                categories[category] = categories.get(category, 0) + (2 if decision == "FAVORITE" else 1)
        ordered_categories = sorted(categories.items(), key=lambda row: (-row[1], row[0]))
        return {
            **counts,
            "decisions": decisions,
            "training_pairs": len(self.training_pairs()),
            "top_categories": ordered_categories[:3],
        }

    def counts(self) -> dict[str, int]:
        with self._connect() as conn:
            return {
                "videos": conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0],
                "candidates": conn.execute("SELECT COUNT(*) FROM candidates").fetchone()[0],
                "feedback": conn.execute("SELECT COUNT(*) FROM feedback").fetchone()[0],
                "preferences": conn.execute("SELECT COUNT(*) FROM preferences").fetchone()[0],
            }
