from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


CATEGORIES = (
    "Person",
    "Action",
    "Landscape",
    "Animal",
    "Plant",
    "Product",
    "Detail",
    "Other",
)


@dataclass(slots=True)
class VideoInfo:
    id: str
    path: str
    duration: float
    width: int
    height: int
    fps: float
    codec: str
    color_primaries: str = ""
    color_transfer: str = ""
    color_space: str = ""
    color_warning: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Shot:
    id: str
    video_id: str
    index: int
    start: float
    end: float
    motion: float = 0.0

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["duration"] = self.duration
        return data


@dataclass(slots=True)
class Candidate:
    id: str
    video_id: str
    shot_id: str
    shot_index: int
    timestamp: float
    preview_path: str
    labels: list[str] = field(default_factory=list)
    label_confidence: dict[str, float] = field(default_factory=dict)
    scores: dict[str, float] = field(default_factory=dict)
    vision_labels: list[dict[str, Any]] = field(default_factory=list)
    rejected: bool = False
    reject_reasons: list[str] = field(default_factory=list)
    hash64: str = ""
    rank: int | None = None
    duplicate_of: str | None = None
    aspect_ratio: str = "original"
    crop_box: list[float] = field(default_factory=lambda: [0.0, 0.0, 1.0, 1.0])

    @property
    def final_score(self) -> float:
        return float(self.scores.get("final", 0.0))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Candidate":
        fields = cls.__dataclass_fields__
        return cls(**{key: value for key, value in data.items() if key in fields})


@dataclass(slots=True)
class AnalysisResult:
    video: VideoInfo
    shots: list[Shot]
    candidates: list[Candidate]
    cache_dir: str
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "video": self.video.to_dict(),
            "shots": [shot.to_dict() for shot in self.shots],
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "cache_dir": self.cache_dir,
            "elapsed_seconds": self.elapsed_seconds,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnalysisResult":
        video = VideoInfo(**data["video"])
        shots = [Shot(**{k: v for k, v in row.items() if k != "duration"}) for row in data["shots"]]
        candidates = [Candidate.from_dict(row) for row in data["candidates"]]
        return cls(video, shots, candidates, data["cache_dir"], data.get("elapsed_seconds", 0.0))


def ensure_path(value: str | Path) -> Path:
    return value if isinstance(value, Path) else Path(value)
