import shutil
import subprocess

import cv2
import pytest

from framepick.media import export_frame


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
