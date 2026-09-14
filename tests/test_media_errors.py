import pytest

from framepick.media import MediaError, probe_video


def test_missing_video_reports_a_media_error(tmp_path):
    with pytest.raises(MediaError):
        probe_video(tmp_path / "missing.mp4")

