from __future__ import annotations

import logging
from pathlib import Path

from scenedetect import AdaptiveDetector, SceneManager, open_video

from .models import Shot, VideoInfo

LOGGER = logging.getLogger(__name__)


def detect_shots(video: VideoInfo, threshold: float = 27.0, min_scene_seconds: float = 0.65) -> list[Shot]:
    """Detect content cuts. Always returns at least one bounded shot."""
    frame_rate = max(1.0, video.fps)
    minimum_frames = max(2, int(min_scene_seconds * frame_rate))
    try:
        stream = open_video(video.path)
        manager = SceneManager()
        manager.auto_downscale = True
        manager.add_detector(
            AdaptiveDetector(
                adaptive_threshold=max(1.5, threshold / 10.0),
                min_scene_len=minimum_frames,
                window_width=2,
                min_content_val=max(8.0, threshold * 0.45),
            )
        )
        manager.detect_scenes(stream, show_progress=False)
        scene_list = manager.get_scene_list(start_in_scene=True)
    except Exception as exc:
        LOGGER.warning("Scene detection failed; using one shot: %s", exc)
        scene_list = []

    bounds: list[tuple[float, float]] = []
    for start, end in scene_list:
        start_seconds = max(0.0, start.get_seconds())
        end_seconds = min(video.duration, end.get_seconds())
        if end_seconds - start_seconds >= 0.08:
            bounds.append((start_seconds, end_seconds))
    if not bounds:
        bounds = [(0.0, video.duration)]
    if bounds[0][0] > 0.08:
        bounds.insert(0, (0.0, bounds[0][0]))
    if video.duration - bounds[-1][1] > 0.08:
        bounds.append((bounds[-1][1], video.duration))
    return [
        Shot(id=f"{video.id}-s{index:04d}", video_id=video.id, index=index, start=start, end=end)
        for index, (start, end) in enumerate(bounds)
    ]
