from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np

from .models import VideoInfo

LOGGER = logging.getLogger(__name__)


class MediaError(RuntimeError):
    pass


def resolve_executable(name: str) -> str:
    """Resolve media tools even when a macOS Finder launch supplies a minimal PATH."""
    if Path(name).is_absolute():
        return name
    override = os.environ.get(f"FRAMEPICK_{name.upper()}")
    if override and Path(override).is_file():
        return override
    discovered = shutil.which(name)
    if discovered:
        return discovered
    for directory in ("/opt/homebrew/bin", "/usr/local/bin", "/usr/bin"):
        candidate = Path(directory) / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return name


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    command = [resolve_executable(command[0]), *command[1:]]
    LOGGER.debug("Running: %s", command)
    try:
        return subprocess.run(command, check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise MediaError(f"找不到视频组件：{Path(command[0]).name}。请重新运行“安装 PickerRoy.command”。") from exc
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.strip()[-1500:] if exc.stderr else str(exc)
        raise MediaError(f"视频处理失败：{message}") from exc


def _fraction(value: str | None) -> float:
    if not value or value in {"0/0", "N/A"}:
        return 0.0
    if "/" in value:
        a, b = value.split("/", 1)
        return float(a) / float(b) if float(b) else 0.0
    return float(value)


def probe_video(path: str | Path) -> VideoInfo:
    source = Path(path).expanduser().resolve()
    completed = _run([
        "ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(source)
    ])
    data = json.loads(completed.stdout)
    video_stream = next((row for row in data.get("streams", []) if row.get("codec_type") == "video"), None)
    if not video_stream:
        raise MediaError(f"文件中没有可读取的视频轨道：{source.name}")
    duration = float(video_stream.get("duration") or data.get("format", {}).get("duration") or 0)
    if duration <= 0:
        raise MediaError(f"无法读取视频时长：{source.name}")
    transfer = video_stream.get("color_transfer", "")
    primaries = video_stream.get("color_primaries", "")
    color_space = video_stream.get("color_space", "")
    warning = ""
    if transfer in {"smpte2084", "arib-std-b67"} or primaries == "bt2020":
        warning = "检测到 HDR/BT.2020 视频；导出会保持 FFmpeg 解码后的画面，但建议检查颜色。"
    signature = f"{source}:{source.stat().st_size}:{source.stat().st_mtime_ns}".encode()
    return VideoInfo(
        id=hashlib.sha1(signature).hexdigest()[:16],
        path=str(source),
        duration=duration,
        width=int(video_stream.get("width", 0)),
        height=int(video_stream.get("height", 0)),
        fps=_fraction(video_stream.get("avg_frame_rate")) or _fraction(video_stream.get("r_frame_rate")) or 30.0,
        codec=video_stream.get("codec_name", "unknown"),
        color_primaries=primaries,
        color_transfer=transfer,
        color_space=color_space,
        color_warning=warning,
    )


def extract_preview(source: str | Path, timestamp: float, destination: str | Path, width: int = 960) -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    _run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{max(0, timestamp):.6f}",
        "-i", str(source), "-frames:v", "1", "-vf", f"scale='min({width},iw)':-2:flags=lanczos",
        "-q:v", "2", "-y", str(destination),
    ])
    if not destination.exists() or destination.stat().st_size == 0:
        raise MediaError(f"无法生成 {timestamp:.3f} 秒处的预览图")
    return destination


def export_frame(source: str | Path, timestamp: float, destination: str | Path, image_format: str = "PNG") -> Path:
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    codec_args = ["-compression_level", "3"] if image_format.upper() == "PNG" else ["-q:v", "1"]
    _run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{max(0, timestamp):.6f}",
        "-i", str(source), "-map", "0:v:0", "-frames:v", "1", *codec_args, "-y", str(destination),
    ])
    return destination


def read_image(path: str | Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None or image.size == 0:
        raise MediaError(f"无法解码抽取的画面：{path}")
    return image


def estimate_motion(source: str | Path, start: float, end: float, preview_dir: Path) -> float:
    duration = max(0.01, end - start)
    margin = min(0.12, duration * 0.08)
    times = np.linspace(start + margin, max(start + margin, end - margin), 4)
    grays: list[np.ndarray] = []
    for index, timestamp in enumerate(times):
        output = preview_dir / f"motion_{start:.3f}_{index}.jpg"
        try:
            extract_preview(source, float(timestamp), output, width=320)
            frame = read_image(output)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            grays.append(gray)
        except MediaError:
            continue
        finally:
            output.unlink(missing_ok=True)
    if len(grays) < 2:
        return 0.0
    values = []
    for previous, current in zip(grays, grays[1:]):
        previous = cv2.GaussianBlur(previous, (5, 5), 0)
        current = cv2.GaussianBlur(current, (5, 5), 0)
        diff = cv2.absdiff(previous, current)
        values.append(float(np.percentile(diff, 75)) / 70.0)
    return float(np.clip(np.mean(values), 0.0, 1.0))


def candidate_timestamps(start: float, end: float, motion: float, min_count: int, max_count: int,
                         base_interval: float, dynamic_interval: float) -> list[float]:
    duration = max(0.01, end - start)
    interval = base_interval + (dynamic_interval - base_interval) * float(np.clip(motion, 0, 1))
    count = int(math.ceil(duration / max(interval, 0.05))) + 1
    count = max(min_count, min(max_count, count))
    margin = min(0.10, duration * 0.06)
    if count == 1:
        return [start + duration / 2]
    values = np.linspace(start + margin, max(start + margin, end - margin), count)
    return [round(float(value), 6) for value in values]
