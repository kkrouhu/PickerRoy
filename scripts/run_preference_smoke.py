from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from framepick.config import AnalysisConfig
from framepick.database import FeedbackStore
from framepick.pipeline import VideoAnalyzer


def main() -> int:
    parser = argparse.ArgumentParser(description="验证 A/B 偏好会在下一次分析中参与排序。")
    parser.add_argument("video", type=Path)
    parser.add_argument("data_dir", type=Path)
    args = parser.parse_args()

    store = FeedbackStore(args.data_dir / "pickerroy.sqlite3")
    config = AnalysisConfig(max_candidates_per_shot=5, max_results_per_video=12)
    first = VideoAnalyzer(args.data_dir, config, store).analyze(args.video)
    grouped = defaultdict(list)
    for candidate in first.candidates:
        if not candidate.rejected:
            grouped[candidate.shot_id].append(candidate)
    pair = next((items[:2] for items in grouped.values() if len(items) >= 2), None)
    if not pair:
        raise RuntimeError("测试视频没有可比较的同镜头候选画面")
    a, b = pair
    winner = max(pair, key=lambda item: item.scores.get("social_popularity", 0.5))
    store.record_preference(a, b, winner)

    second = VideoAnalyzer(args.data_dir, config, store).analyze(args.video)
    learned = [item for item in second.candidates if "personal_preference" in item.scores]
    if not learned:
        raise RuntimeError("第二次分析没有生成个人偏好分")
    print(json.dumps({
        "preferences": store.counts()["preferences"],
        "learned_candidates": len(learned),
        "sample_count_in_scores": learned[0].scores["personal_preference_samples"],
        "winner": winner.id,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
