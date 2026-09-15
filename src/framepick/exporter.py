from __future__ import annotations

import os
import re
import shutil
import tempfile
from pathlib import Path

import cv2

from .media import export_frame
from .models import Candidate, VideoInfo
from .quality import optimized_export_image


def safe_stem(value: str) -> str:
    cleaned = re.sub(r"[^\w.-]+", "_", value, flags=re.UNICODE).strip("._")
    return cleaned or "video"


def _publish_without_overwriting(staged: Path, requested: Path) -> Path:
    """Claim a fresh name exclusively; never truncate an existing export."""
    number = 1
    while True:
        path = requested if number == 1 else requested.with_name(f"{requested.stem}_{number}{requested.suffix}")
        try:
            output = path.open("xb")
        except FileExistsError:
            number += 1
            continue
        owned = os.fstat(output.fileno())
        try:
            with output, staged.open("rb") as source:
                shutil.copyfileobj(source, output)
        except BaseException:
            # Remove only the file this attempt created, never a replacement or
            # symlink another process may have put at this path in the meantime.
            try:
                current = path.lstat()
                if (current.st_dev, current.st_ino) == (owned.st_dev, owned.st_ino):
                    path.unlink()
            except FileNotFoundError:
                pass
            raise
        return path


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
        requested = destination / f"{stem}_{millis:010d}ms_{item.id[-5:]}{suffix}{extension}"
        staged_path: Path | None = None
        temporary_path: Path | None = None
        try:
            # Decode/encode into our own temporary file first. A failure before
            # publication leaves no placeholder bearing the user's export name.
            with tempfile.NamedTemporaryFile(prefix=".pickerroy_export_", suffix=extension,
                                             dir=destination, delete=False) as staged:
                staged_path = Path(staged.name)
            if not optimized:
                export_frame(video.path, item.timestamp, staged_path, image_format, item.crop_box)
            else:
                with tempfile.NamedTemporaryFile(prefix="pickerroy_", suffix=".png", delete=False) as temporary:
                    temporary_path = Path(temporary.name)
                export_frame(video.path, item.timestamp, temporary_path, "PNG", item.crop_box)
                source = cv2.imread(str(temporary_path), cv2.IMREAD_COLOR)
                if source is None or source.size == 0:
                    raise RuntimeError("无法读取待增强的画面")
                enhanced = optimized_export_image(source, video.width, video.height)
                params = [cv2.IMWRITE_PNG_COMPRESSION, 3] if image_format.upper() == "PNG" else [cv2.IMWRITE_JPEG_QUALITY, 96]
                ok, encoded = cv2.imencode(extension, enhanced, params)
                if not ok:
                    raise RuntimeError("无法编码增强后的画面")
                encoded.tofile(str(staged_path))
            path = _publish_without_overwriting(staged_path, requested)
        finally:
            if temporary_path:
                temporary_path.unlink(missing_ok=True)
            if staged_path:
                staged_path.unlink(missing_ok=True)
        exported.append(path)
    return exported
