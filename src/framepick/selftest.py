from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .config import AnalysisConfig
from .database import FeedbackStore
from .exporter import export_candidates
from .logging_setup import configure_logging
from .pipeline import VideoAnalyzer
from .runtime import runtime_checks, runtime_ready


def run_self_test(video: str | Path, output_dir: str | Path) -> Path:
    """Exercise bundled tools, model inference, ranking, database and export."""
    source = Path(video).expanduser().resolve()
    target = Path(output_dir).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    checks = runtime_checks()
    if not runtime_ready(checks):
        raise RuntimeError("视频运行环境未就绪")
    configure_logging(target)
    store = FeedbackStore(target / "pickerroy-self-test.sqlite3")
    result = VideoAnalyzer(target, AnalysisConfig(max_results_per_video=12), store).analyze(source)
    visible = [item for item in result.candidates if item.rank is not None and not item.rejected and not item.duplicate_of]
    exported = export_candidates(result.video, visible[:1], target / "exports", "PNG") if visible else []
    optimized = export_candidates(
        result.video, visible[:1], target / "exports-optimized", "JPEG", optimized=True
    ) if visible else []
    report = {
        "success": bool(visible and exported and optimized),
        "video": source.name,
        "shots": len(result.shots),
        "candidates": len(result.candidates),
        "recommended": len(visible),
        "exports": [str(path) for path in exported],
        "optimized_exports": [str(path) for path in optimized],
        "runtime": [asdict(row) for row in checks],
        "elapsed_seconds": result.elapsed_seconds,
    }
    report_path = target / "self-test-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not report["success"]:
        raise RuntimeError("独立应用自检没有生成推荐画面或导出文件")
    return report_path
