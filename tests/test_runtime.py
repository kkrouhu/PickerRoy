from framepick.runtime import RuntimeCheck, runtime_ready


def test_runtime_requires_both_video_tools():
    assert runtime_ready([
        RuntimeCheck("ffmpeg", True, "ok"),
        RuntimeCheck("ffprobe", True, "ok"),
        RuntimeCheck("model", False, "fallback"),
    ])
    assert not runtime_ready([
        RuntimeCheck("ffmpeg", True, "ok"),
        RuntimeCheck("ffprobe", False, "missing"),
    ])
