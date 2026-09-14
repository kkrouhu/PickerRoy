from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable, Iterable
from pathlib import Path

from .classification import build_classifier, categories_from_observations, face_region_sharpness
from .config import ASPECT_RATIOS, AnalysisConfig, VIDEO_EXTENSIONS
from .database import FeedbackStore
from .media import candidate_timestamps, estimate_motion, extract_preview, probe_video, read_image, write_image
from .models import AnalysisResult, Candidate
from .quality import composition_metrics, perceptual_hash, smart_crop_to_aspect, technical_metrics, temporal_motion_series
from .ranking import apply_temporal_peaks, diversity_rank, mark_duplicates, score_candidates
from .scene import detect_shots

LOGGER = logging.getLogger(__name__)
ProgressCallback = Callable[[dict], None]


def discover_videos(inputs: Iterable[str | Path]) -> list[Path]:
    paths: list[Path] = []
    seen: set[Path] = set()
    for raw in inputs:
        path = Path(raw).expanduser().resolve()
        candidates = path.rglob("*") if path.is_dir() else [path]
        for candidate in candidates:
            if candidate.is_file() and candidate.suffix.lower() in VIDEO_EXTENSIONS and candidate not in seen:
                seen.add(candidate)
                paths.append(candidate)
    return sorted(paths, key=lambda value: value.name.lower())


class VideoAnalyzer:
    def __init__(self, data_dir: str | Path, config: AnalysisConfig | None = None,
                 store: FeedbackStore | None = None, classifier=None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config = config or AnalysisConfig()
        self.store = store
        self.classifier = classifier or build_classifier()

    def analyze(self, video_path: str | Path, progress: ProgressCallback | None = None) -> AnalysisResult:
        started = time.monotonic()
        video = probe_video(video_path)
        ratio_key = self.config.aspect_ratio.replace(":", "x")
        cache_dir = self.data_dir / "cache" / video.id / ratio_key
        previews = cache_dir / "previews"
        previews.mkdir(parents=True, exist_ok=True)
        self._emit(progress, stage="scene_detection", video=Path(video.path).name, progress=0.02)
        shots = detect_shots(video, self.config.scene_threshold, self.config.min_scene_seconds)
        all_candidates: list[Candidate] = []
        total_shots = len(shots)
        for shot_number, shot in enumerate(shots, 1):
            shot_candidates: list[Candidate] = []
            self._emit(
                progress, stage="sampling", video=Path(video.path).name, shot=shot_number,
                shots=total_shots, candidates=len(all_candidates), progress=0.05 + 0.80 * (shot_number - 1) / total_shots,
            )
            shot.motion = estimate_motion(video.path, shot.start, shot.end, previews)
            times = candidate_timestamps(
                shot.start, shot.end, shot.motion,
                self.config.min_candidates_per_shot, self.config.max_candidates_per_shot,
                self.config.base_sample_interval, self.config.dynamic_sample_interval,
            )
            for local_index, timestamp in enumerate(times):
                candidate_id = f"{shot.id}-{ratio_key}-f{local_index:04d}"
                preview_path = previews / f"{candidate_id}.jpg"
                candidate = Candidate(
                    id=candidate_id,
                    video_id=video.id,
                    shot_id=shot.id,
                    shot_index=shot.index,
                    timestamp=timestamp,
                    preview_path=str(preview_path),
                    aspect_ratio=self.config.aspect_ratio,
                )
                try:
                    extract_preview(video.path, timestamp, preview_path, self.config.preview_width)
                    image = read_image(preview_path)
                    image, crop_box = smart_crop_to_aspect(image, ASPECT_RATIOS.get(self.config.aspect_ratio))
                    candidate.crop_box = crop_box
                    if crop_box != [0.0, 0.0, 1.0, 1.0]:
                        write_image(preview_path, image)
                    scores, reasons = technical_metrics(image, shot.motion)
                    scores.update(composition_metrics(image))
                    try:
                        observations, face_count = self.classifier.classify(preview_path)
                    except Exception as exc:
                        # Semantic classification is useful but non-critical. Never discard an otherwise
                        # good frame because an optional classifier failed.
                        LOGGER.warning("Semantic classification failed at %.3fs; continuing: %s", timestamp, exc)
                        observations, face_count = [], 0
                    scores["face_count"] = float(face_count)
                    scores["face_quality"] = face_region_sharpness(image, face_count)
                    height, width = image.shape[:2]
                    labels, confidence = categories_from_observations(
                        observations, face_count, shot.motion, scores.get("edge_density", 0), width / max(height, 1)
                    )
                    candidate.labels = labels
                    candidate.label_confidence = confidence
                    candidate.vision_labels = observations[:12]
                    candidate.scores = scores
                    candidate.reject_reasons = reasons
                    candidate.rejected = bool(reasons) or scores.get("technical", 0) < self.config.min_technical_score
                    if candidate.rejected and not candidate.reject_reasons:
                        candidate.reject_reasons.append("low_technical_score")
                    candidate.hash64 = perceptual_hash(image)
                except Exception as exc:
                    LOGGER.exception("Candidate failed at %.3fs in %s", timestamp, video.path)
                    candidate.rejected = True
                    candidate.reject_reasons = ["decode_or_analysis_error"]
                    candidate.scores = {"technical": 0.0, "final": 0.0}
                    candidate.labels = ["Other"]
                all_candidates.append(candidate)
                shot_candidates.append(candidate)
            valid_candidates = [item for item in shot_candidates if Path(item.preview_path).exists() and item.scores]
            try:
                local_motion = temporal_motion_series([read_image(item.preview_path) for item in valid_candidates])
                for item, value in zip(valid_candidates, local_motion):
                    item.scores["shot_motion"] = shot.motion
                    item.scores["local_motion"] = value
                    item.scores["motion"] = float(0.35 * shot.motion + 0.65 * value)
            except Exception as exc:
                LOGGER.warning("Could not refine temporal motion for shot %s: %s", shot.id, exc)

        self._emit(progress, stage="ranking", video=Path(video.path).name, shots=total_shots,
                   candidates=len(all_candidates), progress=0.88)
        apply_temporal_peaks(all_candidates)
        score_candidates(all_candidates, self.config.mode)
        mark_duplicates(all_candidates, self.config.duplicate_hamming_distance)
        ranked = diversity_rank(all_candidates, self.config.max_results_per_video)
        hidden = [item for item in all_candidates if item not in ranked]
        result = AnalysisResult(
            video=video,
            shots=shots,
            candidates=ranked + hidden,
            cache_dir=str(cache_dir),
            elapsed_seconds=time.monotonic() - started,
        )
        manifest = cache_dir / "analysis.json"
        manifest.write_text(json.dumps(result.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        if self.store:
            self.store.save_analysis(result)
        self._emit(progress, stage="done", video=Path(video.path).name, shots=total_shots,
                   candidates=len(ranked), progress=1.0)
        return result

    @staticmethod
    def _emit(callback: ProgressCallback | None, **payload) -> None:
        if callback:
            callback(payload)


def load_analysis(path: str | Path) -> AnalysisResult:
    return AnalysisResult.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
