from framepick.database import FeedbackStore
from framepick.models import AnalysisResult, Candidate, Shot, VideoInfo


def make_result(tmp_path):
    video = VideoInfo("v", str(tmp_path / "v.mp4"), 2.0, 1920, 1080, 30.0, "h264")
    shot = Shot("s", "v", 0, 0, 2)
    candidate = Candidate(
        "c", "v", "s", 0, 1.0, str(tmp_path / "c.jpg"), ["Person"], {"Person": 0.8}, {"final": 0.8}, hash64="abcd"
    )
    return AnalysisResult(video, [shot], [candidate], str(tmp_path))


def test_feedback_and_pairwise_preferences_are_persisted(tmp_path):
    store = FeedbackStore(tmp_path / "feedback.sqlite3")
    result = make_result(tmp_path)
    store.save_analysis(result)
    candidate = result.candidates[0]
    second = Candidate("c2", "v", "s", 0, 1.1, "c2.jpg", ["Person"], {}, {"final": 0.7})
    result.candidates.append(second)
    store.save_analysis(result)
    store.record_feedback(candidate, "FAVORITE")
    store.record_preference(candidate, second, candidate)
    assert store.latest_feedback()["c"] == "FAVORITE"
    pairs = store.preference_pairs()
    assert [(winner.id, loser.id) for winner, loser in pairs] == [("c", "c2")]
    # Re-analysis updates candidate rows in place so existing pairwise choices remain valid.
    store.save_analysis(result)
    assert [(winner.id, loser.id) for winner, loser in store.preference_pairs()] == [("c", "c2")]
    assert store.counts() == {"videos": 1, "candidates": 2, "feedback": 1, "preferences": 1}
