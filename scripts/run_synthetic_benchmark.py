from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from framepick.config import AnalysisConfig
from framepick.database import FeedbackStore
from framepick.evaluation import evaluate_result
from framepick.exporter import export_candidates
from framepick.logging_setup import configure_logging
from framepick.pipeline import VideoAnalyzer


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", default="work/first-debug")
    args = parser.parse_args()
    work_dir = Path(args.work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    video = work_dir / "synthetic-benchmark.mp4"
    subprocess.run([str(Path(__file__).with_name("make_synthetic_benchmark.sh")), str(video)], check=True)
    data = work_dir / "data"
    configure_logging(data)
    store = FeedbackStore(data / "framepick.sqlite3")
    result = VideoAnalyzer(data, AnalysisConfig(max_results_per_video=24), store).analyze(video)
    visible = [item for item in result.candidates if item.rank is not None and not item.rejected]
    chosen = visible[: min(3, len(visible))]
    if chosen:
        store.record_feedback(chosen[0], "KEEP")
    pair = next(
        (
            (left, right)
            for left in result.candidates
            for right in result.candidates
            if left.id < right.id and left.shot_id == right.shot_id and not left.rejected and not right.rejected
        ),
        None,
    )
    if pair:
        store.record_preference(pair[0], pair[1], pair[0])
    exports = export_candidates(result.video, chosen[:2], work_dir / "exports", "PNG")
    targets = [
        {"timestamp": 1.5, "tolerance_ms": 1500},
        {"timestamp": 5.5, "tolerance_ms": 1500},
        {"timestamp": 8.5, "tolerance_ms": 1500},
    ]
    metrics = evaluate_result(result, targets)
    report = {
        "video": result.video.to_dict(),
        "shots": len(result.shots),
        "analyzed_candidates": len(result.candidates),
        "recommended": len(visible),
        "technical_rejections": sum(item.rejected for item in result.candidates),
        "duplicates": sum(bool(item.duplicate_of) for item in result.candidates),
        "exports": [str(path) for path in exports],
        "database": store.counts(),
        "elapsed_seconds": result.elapsed_seconds,
        "metrics": metrics,
        "note": "Synthetic engineering benchmark; not a real-world aesthetic accuracy claim.",
    }
    report_path = work_dir / "benchmark-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
