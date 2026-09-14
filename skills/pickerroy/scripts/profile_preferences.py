#!/usr/bin/env python3
"""Export a privacy-preserving summary of a PickerRoy preference database."""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import Counter
from pathlib import Path


def summarize(path: Path) -> dict:
    with sqlite3.connect(path) as connection:
        table_names = {
            row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        required = {"videos", "candidates", "feedback", "preferences"}
        if not required.issubset(table_names):
            raise ValueError("这不是可识别的 PickerRoy 偏好数据库")
        counts = {
            name: connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
            for name in sorted(required)
        }
        rows = connection.execute(
            """SELECT candidate.categories_json, candidate.scores_json, feedback.decision
            FROM feedback
            JOIN candidates candidate ON candidate.id=feedback.candidate_id
            JOIN (SELECT candidate_id, MAX(id) AS max_id FROM feedback GROUP BY candidate_id) latest
              ON latest.max_id=feedback.id
            WHERE feedback.decision != 'CLEAR'"""
        ).fetchall()

    decisions = Counter()
    liked_categories = Counter()
    score_totals: Counter[str] = Counter()
    score_counts: Counter[str] = Counter()
    safe_features = {
        "technical", "sharpness", "exposure", "visual_balance", "rule_of_thirds",
        "portrait_aesthetic", "landscape_aesthetic", "social_popularity", "motion",
    }
    for raw_categories, raw_scores, decision in rows:
        decisions[decision] += 1
        if decision in {"KEEP", "FAVORITE"}:
            weight = 2 if decision == "FAVORITE" else 1
            liked_categories.update({name: weight for name in json.loads(raw_categories)})
            for name, value in json.loads(raw_scores).items():
                if name in safe_features and isinstance(value, (int, float)):
                    score_totals[name] += float(value)
                    score_counts[name] += 1
    averages = {
        name: round(score_totals[name] / score_counts[name], 4)
        for name in sorted(score_counts)
    }
    return {
        "schema": "pickerroy-preference-profile-v1",
        "database": {**counts, "latest_decisions": dict(sorted(decisions.items()))},
        "liked_categories": liked_categories.most_common(8),
        "liked_frame_feature_averages": averages,
        "privacy": "No file paths, images, video frames, candidate IDs, or timestamps are included.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize a PickerRoy preference database without media or paths")
    parser.add_argument("database", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = summarize(args.database.expanduser().resolve())
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
