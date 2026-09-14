from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import AnalysisConfig
from .database import FeedbackStore
from .logging_setup import configure_logging
from .pipeline import VideoAnalyzer, discover_videos


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze videos with FramePick Local")
    parser.add_argument("inputs", nargs="+", help="Video files or folders")
    parser.add_argument("--data-dir", default=".framepick-data", help="Cache, database, and log directory")
    parser.add_argument("--mode", default="Balanced", choices=["Balanced", "Portrait", "Action", "Landscape", "Product"])
    parser.add_argument("--json", action="store_true", help="Print machine-readable summary")
    args = parser.parse_args(argv)
    data_dir = Path(args.data_dir).resolve()
    configure_logging(data_dir)
    store = FeedbackStore(data_dir / "framepick.sqlite3")
    analyzer = VideoAnalyzer(data_dir, AnalysisConfig.for_mode(args.mode), store)
    videos = discover_videos(args.inputs)
    if not videos:
        parser.error("No supported videos were found")
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

