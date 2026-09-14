from __future__ import annotations

import re
from pathlib import Path

from .media import export_frame
from .models import Candidate, VideoInfo


def safe_stem(value: str) -> str:
    cleaned = re.sub(r"[^\w.-]+", "_", value, flags=re.UNICODE).strip("._")
    return cleaned or "video"


def export_candidates(video: VideoInfo, candidates: list[Candidate], destination: str | Path,
                      image_format: str = "PNG") -> list[Path]:
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    extension = ".png" if image_format.upper() == "PNG" else ".jpg"
    stem = safe_stem(Path(video.path).stem)
    exported: list[Path] = []
    for item in candidates:
        millis = round(item.timestamp * 1000)
        path = destination / f"{stem}_{millis:010d}ms_{item.id[-5:]}{extension}"
        export_frame(video.path, item.timestamp, path, image_format)
        exported.append(path)
    return exported

