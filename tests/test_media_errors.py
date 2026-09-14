import os

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


def test_bundled_executable_is_preferred(tmp_path, monkeypatch):
    executable_name = "ffprobe.exe" if os.name == "nt" else "ffprobe"
    bundled = tmp_path / "bin" / executable_name
    bundled.parent.mkdir()
    bundled.write_text("test")
    bundled.chmod(0o755)
    monkeypatch.setattr("sys._MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setenv("PATH", "")
    monkeypatch.delenv("FRAMEPICK_FFPROBE", raising=False)
    assert resolve_executable("ffprobe") == str(bundled)
