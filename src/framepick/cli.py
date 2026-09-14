from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import AnalysisConfig
from .database import FeedbackStore
from .logging_setup import configure_logging
from .pipeline import VideoAnalyzer, discover_videos


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="使用 PickerRoy 分析视频")
    parser.add_argument("inputs", nargs="+", help="视频文件或文件夹")
    parser.add_argument("--data-dir", default=".pickerroy-data", help="缓存、数据库和日志目录")
    parser.add_argument("--mode", default="Balanced", choices=["Balanced", "Portrait", "Action", "Landscape", "Product"])
    parser.add_argument(
        "--aspect-ratio", default="original",
        choices=["original", "1:1", "3:2", "2:3", "4:3", "3:4", "16:9", "9:16"],
        help="生成画面比例",
    )
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式结果")
    args = parser.parse_args(argv)
    data_dir = Path(args.data_dir).resolve()
    configure_logging(data_dir)
    store = FeedbackStore(data_dir / "framepick.sqlite3")
    analyzer = VideoAnalyzer(data_dir, AnalysisConfig.for_mode(args.mode, args.aspect_ratio), store)
    videos = discover_videos(args.inputs)
    if not videos:
        parser.error("没有找到支持的视频文件")
    summaries = []
    for path in videos:
        result = analyzer.analyze(path)
        visible = [item for item in result.candidates if item.rank is not None and not item.rejected]
        summary = {
            "video": result.video.path,
            "shots": len(result.shots),
            "recommended": len(visible),
            "analyzed_candidates": len(result.candidates),
            "rejected": sum(item.rejected for item in result.candidates),
            "duplicates": sum(bool(item.duplicate_of) for item in result.candidates),
            "elapsed_seconds": round(result.elapsed_seconds, 3),
            "analysis": str(Path(result.cache_dir) / "analysis.json"),
        }
        summaries.append(summary)
        if not args.json:
            print(f"{path.name}: {summary['shots']} shots, {summary['recommended']} recommendations, {summary['elapsed_seconds']}s")
    if args.json:
        print(json.dumps(summaries, ensure_ascii=False, indent=2))
    return 0
