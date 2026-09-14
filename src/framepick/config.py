from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class AnalysisConfig:
    mode: str = "Balanced"
    aspect_ratio: str = "original"
    scene_threshold: float = 27.0
    min_scene_seconds: float = 0.65
    preview_width: int = 960
    min_candidates_per_shot: int = 3
    max_candidates_per_shot: int = 20
    base_sample_interval: float = 1.15
    dynamic_sample_interval: float = 0.28
    severe_black_fraction: float = 0.80
    severe_white_fraction: float = 0.72
    min_technical_score: float = 0.22
    duplicate_hamming_distance: int = 7
    max_results_per_video: int = 60

    @classmethod
    def for_mode(cls, mode: str, aspect_ratio: str = "original") -> "AnalysisConfig":
        base = cls(mode=mode, aspect_ratio=aspect_ratio)
        choices = {
            "Portrait": dict(max_results_per_video=70),
            "Action": dict(dynamic_sample_interval=0.20, max_candidates_per_shot=28, max_results_per_video=80),
            "Landscape": dict(base_sample_interval=1.45, max_results_per_video=45),
            "Product": dict(base_sample_interval=0.80, max_results_per_video=70),
        }
        return replace(base, **choices.get(mode, {}))


VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".m4v", ".mkv", ".avi", ".webm", ".mts", ".m2ts", ".mxf"
}

ASPECT_RATIOS: dict[str, float | None] = {
    "original": None,
    "1:1": 1.0,
    "3:2": 3 / 2,
    "2:3": 2 / 3,
    "4:3": 4 / 3,
    "3:4": 3 / 4,
    "16:9": 16 / 9,
    "9:16": 9 / 16,
}
