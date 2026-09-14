import pytest

from framepick.media import MediaError, probe_video, resolve_executable


def test_missing_video_reports_a_media_error(tmp_path):
    with pytest.raises(MediaError):
        probe_video(tmp_path / "missing.mp4")


def test_executable_override_works_with_minimal_path(tmp_path, monkeypatch):
    fake = tmp_path / "ffprobe"
    fake.write_text("test")
    fake.chmod(0o755)
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    monkeypatch.setenv("FRAMEPICK_FFPROBE", str(fake))
    assert resolve_executable("ffprobe") == str(fake)
