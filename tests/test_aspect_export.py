import shutil
import subprocess

import cv2
import pytest

from framepick.exporter import export_candidates
from framepick.media import export_frame
from framepick.models import Candidate, VideoInfo


@pytest.mark.integration
def test_full_resolution_export_respects_square_crop(tmp_path):
    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg not installed")
    video = tmp_path / "wide.mp4"
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
            "testsrc2=size=640x360:rate=24:duration=1", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video),
        ],
        check=True,
    )
    output = tmp_path / "square.png"
    export_frame(video, 0.5, output, "PNG", [0.21875, 0.0, 0.5625, 1.0])
    image = cv2.imread(str(output))
    assert image is not None
    assert image.shape[:2] == (360, 360)


@pytest.mark.integration
def test_optimized_export_upscales_a_portrait_crop(tmp_path):
    if not shutil.which("ffmpeg"):
        pytest.skip("FFmpeg not installed")
    video_path = tmp_path / "wide.mp4"
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
            "testsrc2=size=640x360:rate=24:duration=1", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(video_path),
        ],
        check=True,
    )
    video = VideoInfo("v", str(video_path), 1, 640, 360, 24, "h264")
    candidate = Candidate(
        "candidate", "v", "shot", 0, 0.5, "unused.jpg", crop_box=[0.2890625, 0, 0.421875, 1]
    )
    [output] = export_candidates(video, [candidate], tmp_path / "out", "PNG", optimized=True)
    image = cv2.imread(str(output))
    assert image is not None
    assert image.shape[0] > 360
    assert image.shape[1] > 270
    assert output.name.endswith("_optimized.png")
