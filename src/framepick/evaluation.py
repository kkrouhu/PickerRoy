from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean

from .models import AnalysisResult
from .pipeline import load_analysis
from .quality import hamming_distance


def _hit(candidates, targets, limit: int) -> tuple[int, int]:
    matches = 0
    ranked = [item for item in candidates if item.rank is not None and not item.rejected][:limit]
    for target in targets:
        tolerance = float(target.get("tolerance_ms", 400)) / 1000
        timestamp = float(target["timestamp"])
        if any(abs(item.timestamp - timestamp) <= tolerance for item in ranked):
            matches += 1
    return matches, len(targets)


def evaluate_result(result: AnalysisResult, targets: list[dict]) -> dict[str, float]:
    visible = [item for item in result.candidates if item.rank is not None and not item.rejected]
    all_valid = [item for item in result.candidates if not item.rejected]
    all_duplicate_count = sum(bool(item.duplicate_of) for item in result.candidates if not item.rejected)
    visible_duplicate_pairs = sum(
        1
        for index, item in enumerate(visible)
        for other in visible[index + 1:]
        if hamming_distance(item.hash64, other.hash64) <= 7
        and (item.shot_id == other.shot_id or hamming_distance(item.hash64, other.hash64) <= 2)
    )
    rejected = [item for item in result.candidates if item.rejected]
    categories = {label for item in visible for label in item.labels if label != "Other"}
    metrics: dict[str, float] = {}
    for limit in (1, 3, 5, 10):
        hits, target_count = _hit(result.candidates, targets, limit)
        metrics[f"top_{limit}_hit_rate"] = hits / max(target_count, 1)
    metrics["duplicate_rate"] = visible_duplicate_pairs / max(len(visible), 1)
    metrics["source_candidate_duplicate_fraction"] = all_duplicate_count / max(len(all_valid), 1)
    metrics["rejected_technical_failure_rate"] = len(rejected) / max(len(result.candidates), 1)
    metrics["category_coverage"] = len(categories) / 6
    metrics["candidates_presented"] = float(len(visible))
    return metrics


def evaluate_manifest(manifest_path: str | Path) -> dict:
    path = Path(manifest_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for video in payload.get("videos", []):
        analysis_path = (path.parent / video["analysis"]).resolve()
        result = load_analysis(analysis_path)
        metrics = evaluate_result(result, video.get("targets", []))
        rows.append({"name": video.get("name", Path(result.video.path).name), **metrics})
    aggregate: dict[str, float] = {}
    if rows:
        for key in rows[0]:
            if key != "name":
                aggregate[key] = mean(float(row[key]) for row in rows)
    return {"schema_version": 1, "videos": rows, "aggregate": aggregate}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="对照人工标准答案评测 PickerRoy")
    parser.add_argument("manifest", help="人工标准答案 JSON 文件路径")
    parser.add_argument("--output", help="可选的 JSON 报告输出路径")
    args = parser.parse_args(argv)
    report = evaluate_manifest(args.manifest)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    return 0
