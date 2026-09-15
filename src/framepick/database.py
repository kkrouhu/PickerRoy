from __future__ import annotations

import json
import sqlite3
from collections import defaultdict, deque
from collections.abc import Iterator
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
        """Build a bounded, recent-first sample without discarding stored history.

        The latest choice wins within each feedback channel. Different videos
        and A/B versus decision-derived signals take turns, so a large old video
        cannot exhaust the budget before a new video's choices are considered.
        CLEAR removes a candidate from inferred comparisons, not explicit A/B
        history. Historical timestamps have second precision; conflicting A/B
        and labels at the same recorded time favor the explicit comparison.
        """
        if limit <= 0:
            return []
        with self._connect() as conn:
            feedback_rows = conn.execute(
                """SELECT candidate.id, feedback.decision, feedback.created_at, feedback.id
                FROM feedback
                JOIN candidates candidate ON candidate.id=feedback.candidate_id
                JOIN (SELECT candidate_id, MAX(id) AS max_id FROM feedback GROUP BY candidate_id) latest
                  ON latest.max_id=feedback.id
                ORDER BY feedback.id DESC"""
            ).fetchall()
            candidate_rows = conn.execute(
                "SELECT payload_json, rowid FROM candidates ORDER BY rowid DESC"
            ).fetchall()
            preference_rows = conn.execute(
                """SELECT candidate_a_id, candidate_b_id, winner_id, created_at, id
                FROM preferences ORDER BY id DESC"""
            ).fetchall()

        candidates: dict[str, Candidate] = {}
        by_video: dict[str, list[Candidate]] = defaultdict(list)
        candidate_order: dict[str, int] = {}
        for payload, rowid in candidate_rows:
            candidate = Candidate.from_dict(json.loads(payload))
            candidates[candidate.id] = candidate
            by_video[candidate.video_id].append(candidate)
            candidate_order[candidate.video_id] = max(candidate_order.get(candidate.video_id, 0), rowid)
        decisions = {identifier: (decision, timestamp, identifier_order)
                     for identifier, decision, timestamp, identifier_order in feedback_rows}
        decision_candidates: dict[str, list[Candidate]] = defaultdict(list)
        activity: dict[str, tuple[str, int]] = {}
        for identifier, decision, timestamp, identifier_order in feedback_rows:
            candidate = candidates[identifier]
            if decision != "CLEAR":
                decision_candidates[candidate.video_id].append(candidate)
            activity[candidate.video_id] = max(activity.get(candidate.video_id, ("", 0)),
                                               (timestamp, identifier_order))

        def key_for(a: Candidate, b: Candidate) -> tuple[str, str]:
            return tuple(sorted((a.id, b.id)))

        explicit: dict[tuple[str, str], tuple[Candidate, Candidate, str]] = {}
        explicit_by_video: dict[str, list[tuple[Candidate, Candidate]]] = defaultdict(list)
        levels = {"FAVORITE": 2, "KEEP": 1, "REJECT": 0}
        for a_id, b_id, winner_id, timestamp, identifier_order in preference_rows:
            if a_id not in candidates or b_id not in candidates or winner_id not in {a_id, b_id} or a_id == b_id:
                continue
            a, b = candidates[a_id], candidates[b_id]
            key = key_for(a, b)
            if key in explicit or a.video_id != b.video_id or a.shot_id != b.shot_id:
                continue
            winner, loser = (a, b) if winner_id == a_id else (b, a)
            # Prefer newer contradictory labels when their ordering is known.
            # Equal timestamps cannot resolve cross-table order; explicit A/B
            # is the stronger signal and must not be canceled by its reverse.
            a_decision, a_time, _ = decisions.get(a_id, ("", "", 0))
            b_decision, b_time, _ = decisions.get(b_id, ("", "", 0))
            if (a_decision in levels and b_decision in levels
                    and levels[a_decision] != levels[b_decision]
                    and max(a_time, b_time) > timestamp):
                winner, loser = (a, b) if levels[a_decision] > levels[b_decision] else (b, a)
            explicit[key] = (winner, loser, timestamp)
            explicit_by_video[a.video_id].append((winner, loser))
            activity[a.video_id] = max(activity.get(a.video_id, ("", 0)), (timestamp, identifier_order))

        def decision_pairs(video_id: str) -> Iterator[tuple[Candidate, Candidate]]:
            marked = decision_candidates[video_id]
            partners_by_level = {
                level: [item for item in marked if levels[decisions[item.id][0]] != level][:40]
                for level in levels.values()
            }
            neutral_by_shot: dict[str, list[Candidate]] = defaultdict(list)
            for item in by_video[video_id]:
                if item.id not in decisions and not item.rejected and len(neutral_by_shot[item.shot_id]) < 6:
                    neutral_by_shot[item.shot_id].append(item)
            for anchor in marked:
                level = levels[decisions[anchor.id][0]]
                for partner in partners_by_level[level]:
                    yield (anchor, partner) if level > levels[decisions[partner.id][0]] else (partner, anchor)
                if level != 1:
                    for item in neutral_by_shot[anchor.shot_id]:
                        yield (anchor, item) if level == 2 else (item, anchor)

        def take_turns(iterables) -> Iterator[tuple[Candidate, Candidate]]:
            active = deque(iter(iterable) for iterable in iterables)
            while active:
                current = active.popleft()
                try:
                    pair = next(current)
                except StopIteration:
                    continue
                active.append(current)
                yield pair

        # Recent video activity first; source-local IDs and candidate insertion
        # order make ties deterministic without altering the historical schema.
        video_ids = sorted(activity, key=lambda video_id: (*activity[video_id], candidate_order[video_id]), reverse=True)
        streams = [take_turns((explicit_by_video[video_id], decision_pairs(video_id))) for video_id in video_ids]
        pairs: list[tuple[Candidate, Candidate]] = []
        seen: set[tuple[str, str]] = set()
        for winner, loser in take_turns(streams):
            key = key_for(winner, loser)
            if key in seen:
                continue
            seen.add(key)
            if key in explicit:
                winner, loser, _ = explicit[key]
            pairs.append((winner, loser))
            if len(pairs) >= limit:
                break
        return pairs

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
