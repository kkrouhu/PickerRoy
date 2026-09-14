from __future__ import annotations

import re
import tempfile
from pathlib import Path

import cv2

from .media import export_frame
from .models import Candidate, VideoInfo
from .quality import optimized_export_image


def safe_stem(value: str) -> str:
    cleaned = re.sub(r"[^\w.-]+", "_", value, flags=re.UNICODE).strip("._")
    return cleaned or "video"


def export_candidates(video: VideoInfo, candidates: list[Candidate], destination: str | Path,
                      image_format: str = "PNG", optimized: bool = False) -> list[Path]:
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    extension = ".png" if image_format.upper() == "PNG" else ".jpg"
    stem = safe_stem(Path(video.path).stem)
    exported: list[Path] = []
    for item in candidates:
        millis = round(item.timestamp * 1000)
        suffix = "_optimized" if optimized else ""
        path = destination / f"{stem}_{millis:010d}ms_{item.id[-5:]}{suffix}{extension}"
        if not optimized:
            export_frame(video.path, item.timestamp, path, image_format, item.crop_box)
        else:
            temporary_path: Path | None = None
            try:
                with tempfile.NamedTemporaryFile(prefix="pickerroy_", suffix=".png", delete=False) as temporary:
                    temporary_path = Path(temporary.name)
                export_frame(video.path, item.timestamp, temporary_path, "PNG", item.crop_box)
                source = cv2.imread(str(temporary_path), cv2.IMREAD_COLOR)
                if source is None or source.size == 0:
                    raise RuntimeError("无法读取待优化的画面")
                enhanced = optimized_export_image(source, video.width, video.height)
                params = [cv2.IMWRITE_PNG_COMPRESSION, 3] if image_format.upper() == "PNG" else [cv2.IMWRITE_JPEG_QUALITY, 96]
                ok, encoded = cv2.imencode(extension, enhanced, params)
                if not ok:
                    raise RuntimeError("无法编码优化后的画面")
                encoded.tofile(str(path))
            finally:
                if temporary_path:
                    temporary_path.unlink(missing_ok=True)
        exported.append(path)
    return exported
