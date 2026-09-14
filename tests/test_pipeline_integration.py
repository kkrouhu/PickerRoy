import json
import shutil
import subprocess

import pytest

from framepick.config import AnalysisConfig
from framepick.pipeline import VideoAnalyzer, discover_videos


class FakeClassifier:
    name = "test"

    def classify(self, path):
        return [{"label": "outdoor landscape", "confidence": 0.8}], 0


@pytest.mark.integration
def test_scene_to_ranked_candidates(tmp_path):
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        pytest.skip("FFmpeg not installed")
    video = tmp_path / "synthetic-scenes.mp4"
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=24:duration=2",
            "-f", "lavfi", "-i", "smptebars=size=640x360:rate=24:duration=2",
            "-filter_complex", "[0:v][1:v]concat=n=2:v=1:a=0,format=yuv420p[v]",
            "-map", "[v]", "-c:v", "libx264", str(video),
        ],
        check=True,
    )
    config = AnalysisConfig(max_candidates_per_shot=5, max_results_per_video=8)
    result = VideoAnalyzer(tmp_path / "data", config, classifier=FakeClassifier()).analyze(video)
    assert len(result.shots) >= 2
    assert any(item.rank is not None for item in result.candidates)
    assert any("social_popularity" in item.scores for item in result.candidates if not item.rejected)
    assert all(item.preview_path for item in result.candidates)
    manifest = tmp_path / "data" / "cache" / result.video.id / "original" / "analysis.json"
    assert json.loads(manifest.read_text())["schema_version"] == 1
    assert discover_videos([tmp_path]) == [video]
