"""Local preference integration, using synthetic features rather than aesthetic claims.

Only media decoding and feature measurement are replaced. The SQLite feedback
store, pair construction, model fitting, pipeline preference application,
category scoring, duplicate filtering, and final diversity ranking stay real.
No user media, model downloads, Apple services, or shared preference data are used.
"""

from pathlib import Path
import json
import re

import numpy as np
import pytest

from framepick import pipeline
from framepick.config import AnalysisConfig
from framepick.database import FeedbackStore
from framepick.models import AnalysisResult, Candidate, Shot, VideoInfo


TRAITS = (0.1, 0.5, 0.9)
HASHES = ("0000000000000000", "aaaaaaaaaaaaaaaa", "ffffffffffffffff")


def _base_scores() -> dict[str, float]:
    # Color harmony is a learned feature but does not enter the Other baseline
    # score. Identical remaining metrics isolate the effect of personalization.
    return {
        "technical": 0.8,
        "sharpness": 0.7,
        "exposure": 0.7,
        "contrast": 0.6,
        "visual_balance": 0.7,
        "rule_of_thirds": 0.7,
        "face_quality": 0.0,
        "social_popularity": 0.5,
        "motion": 0.0,
    }


def _training_result(directory: Path, count: int = 3, video_id: str = "training") -> AnalysisResult:
    video = VideoInfo(video_id, str(directory / f"{video_id}.mp4"), 3.0, 32, 24, 30.0, "test")
    shot = Shot(f"{video_id}-shot", video.id, 0, 0.0, 3.0)
    candidates = [
        Candidate(
            id=f"{video_id}-{index}", video_id=video.id, shot_id=shot.id,
            shot_index=0, timestamp=index + 0.5,
            preview_path=str(directory / f"training-{index}.png"),
            labels=["Other"], label_confidence={"Other": 1.0},
            scores={**_base_scores(), "color_harmony": trait},
            hash64=HASHES[index],
        )
        for index, trait in enumerate(TRAITS[:count])
    ]
    return AnalysisResult(video, [shot], candidates, str(directory))


def _record_direction(store: FeedbackStore, result: AnalysisResult, prefer_high: bool,
                      signal: str = "combined") -> None:
    low, middle, high = result.candidates
    favorite, rejected = (high, low) if prefer_high else (low, high)
    if signal in {"decisions", "combined"}:
        store.record_feedback(favorite, "FAVORITE")
        store.record_feedback(middle, "KEEP")
        store.record_feedback(rejected, "REJECT")
    if signal in {"ab", "combined"}:
        store.record_preference(low, high, favorite)


@pytest.fixture
def measured_pipeline(monkeypatch):
    """Deterministic future frames; no mocking of the personalization path."""
    frames: dict[str, np.ndarray] = {}

    def probe(path, control=None):
        return VideoInfo("next-video", str(path), 3.0, 32, 24, 30.0, "test")

    def extract(path, timestamp, destination, width, control=None):
        index = int(timestamp)
        frames[str(destination)] = np.full((24, 32, 3), index + 1, dtype=np.uint8)
        # The pipeline legitimately checks for a preview before temporal and
        # popularity measurement. Pixels are supplied by read_image below.
        Path(destination).touch()

    monkeypatch.setattr(pipeline, "probe_video", probe)
    monkeypatch.setattr(pipeline, "detect_shots", lambda video, *args: [
        Shot("next-shot", video.id, 0, 0.0, 3.0)
    ])
    monkeypatch.setattr(pipeline, "estimate_motion", lambda *args: 0.0)
    monkeypatch.setattr(pipeline, "candidate_timestamps", lambda *args: [0.5, 1.5, 2.5])
    monkeypatch.setattr(pipeline, "extract_preview", extract)
    def read(path):
        if str(path) in frames:
            return frames[str(path)].copy()
        # A successfully cropped preview is renamed to its stable identity.
        seek_time = re.search(r"-t(\d+)p(\d{6})-", Path(path).stem)
        assert seek_time is not None
        index = int(float(f"{seek_time[1]}.{seek_time[2]}"))
        return np.full((24, 32, 3), index + 1, dtype=np.uint8)

    monkeypatch.setattr(pipeline, "read_image", read)
    monkeypatch.setattr(pipeline, "technical_metrics", lambda *args: (_base_scores(), []))
    monkeypatch.setattr(pipeline, "composition_metrics", lambda *args: {})
    monkeypatch.setattr(pipeline, "face_region_sharpness", lambda *args: 0.0)
    monkeypatch.setattr(pipeline, "aesthetic_metrics", lambda image, *args: {
        "color_harmony": TRAITS[int(image[0, 0, 0]) - 1]
    })
    monkeypatch.setattr(pipeline, "categories_from_observations", lambda *args: (["Other"], {"Other": 1.0}))
    monkeypatch.setattr(pipeline, "perceptual_hash", lambda image: HASHES[int(image[0, 0, 0]) - 1])
    monkeypatch.setattr(pipeline, "temporal_motion_series", lambda images: [0.0] * len(images))

    class Classifier:
        def classify(self, path):
            return [], 0

    class PopularityScorer:
        def score_path(self, path):
            return 0.0

    def analyze(directory: Path, store: FeedbackStore | None, config: AnalysisConfig | None = None) -> AnalysisResult:
        return pipeline.VideoAnalyzer(
            directory,
            config or AnalysisConfig(max_results_per_video=3),
            store=store,
            classifier=Classifier(),
            popularity_scorer=PopularityScorer(),
        ).analyze(directory / "next.mp4")

    return analyze


def _ranked_traits(result: AnalysisResult) -> list[float]:
    ranked = sorted((item for item in result.candidates if item.rank is not None), key=lambda item: item.rank)
    return [item.scores["color_harmony"] for item in ranked]


@pytest.mark.parametrize("signal, expected_pairs", [("decisions", 3), ("ab", 1), ("combined", 3)])
def test_opposite_local_users_change_later_pipeline_scores_and_actual_ranks(
    tmp_path, measured_pipeline, signal, expected_pairs,
):
    """Opposite feedback affects new candidates, not just stored training rows."""
    training = _training_result(tmp_path)
    stores = [FeedbackStore(tmp_path / name / "preferences.sqlite3") for name in ("user-a", "user-b")]
    assert stores[0].path != stores[1].path
    for store, prefer_high in zip(stores, (True, False)):
        store.save_analysis(training)
        _record_direction(store, training, prefer_high, signal)
        assert len(store.training_pairs()) == expected_pairs

    baseline = measured_pipeline(tmp_path / "no-profile", None)
    assert len({item.final_score for item in baseline.candidates}) == 1
    assert all("personal_preference" not in item.scores for item in baseline.candidates)

    # Reopen the stores to prove the preference source is persisted SQLite data,
    # rather than accidental shared in-memory objects from the training setup.
    results = [
        measured_pipeline(tmp_path / f"next-{index}", FeedbackStore(store.path))
        for index, store in enumerate(stores)
    ]
    assert _ranked_traits(results[0]) == [0.9, 0.5, 0.1]
    assert _ranked_traits(results[1]) == [0.1, 0.5, 0.9]

    for result, prefer_high in zip(results, (True, False)):
        by_trait = {item.scores["color_harmony"]: item for item in result.candidates}
        favorite_trait, rejected_trait = (0.9, 0.1) if prefer_high else (0.1, 0.9)
        favorite, rejected = by_trait[favorite_trait], by_trait[rejected_trait]
        assert favorite.scores["personal_preference"] == 1.0
        assert by_trait[0.5].scores["personal_preference"] == 0.5
        assert rejected.scores["personal_preference"] == 0.0
        assert favorite.scores["personal_preference_raw"] > rejected.scores["personal_preference_raw"]
        assert favorite.final_score > rejected.final_score
        assert all(item.scores["personal_preference_samples"] == expected_pairs for item in result.candidates)
        assert all(item.video_id == "next-video" and not item.rejected and not item.duplicate_of
                   for item in result.candidates)


def test_changed_latest_decisions_affect_next_analysis_without_changing_other_user(tmp_path, measured_pipeline):
    training = _training_result(tmp_path)
    user_a = FeedbackStore(tmp_path / "user-a.sqlite3")
    user_b = FeedbackStore(tmp_path / "user-b.sqlite3")
    for store in (user_a, user_b):
        store.save_analysis(training)
        _record_direction(store, training, True, "decisions")

    before = measured_pipeline(tmp_path / "before", user_a)
    assert _ranked_traits(before) == [0.9, 0.5, 0.1]
    _record_direction(user_a, training, False, "decisions")

    after = measured_pipeline(tmp_path / "after", FeedbackStore(user_a.path))
    unchanged = measured_pipeline(tmp_path / "other-user", FeedbackStore(user_b.path))
    assert _ranked_traits(after) == [0.1, 0.5, 0.9]
    assert _ranked_traits(unchanged) == [0.9, 0.5, 0.1]
    assert user_a.latest_feedback()["training-0"] == "FAVORITE"
    assert user_b.latest_feedback()["training-0"] == "REJECT"
    assert len(user_a.training_pairs()) == len(user_b.training_pairs()) == 3


def test_isolated_favorite_without_comparable_candidates_does_not_invent_learning(tmp_path, measured_pipeline):
    store = FeedbackStore(tmp_path / "single.sqlite3")
    training = _training_result(tmp_path, count=1)
    store.save_analysis(training)
    store.record_feedback(training.candidates[0], "FAVORITE")
    assert store.personalization_stats()["decisions"]["FAVORITE"] == 1
    assert store.training_pairs() == []
    result = measured_pipeline(tmp_path / "next", store)
    assert all("personal_preference" not in item.scores for item in result.candidates)
    assert len({item.final_score for item in result.candidates}) == 1


def test_latest_reversed_ab_choice_replaces_training_direction_but_preserves_history(tmp_path, measured_pipeline):
    store = FeedbackStore(tmp_path / "ab.sqlite3")
    training = _training_result(tmp_path)
    store.save_analysis(training)
    low, _, high = training.candidates
    store.record_preference(low, high, high)
    assert _ranked_traits(measured_pipeline(tmp_path / "before", store)) == [0.9, 0.5, 0.1]
    store.record_preference(high, low, high)
    store.record_preference(low, high, low)

    assert len(store.preference_pairs()) == 3  # No historical rows were removed.
    assert [(winner.id, loser.id) for winner, loser in store.training_pairs()] == [(low.id, high.id)]
    assert _ranked_traits(measured_pipeline(tmp_path / "after", store)) == [0.1, 0.5, 0.9]


@pytest.mark.parametrize("clear_index", [0, 1])
def test_clear_removes_latest_label_without_reintroducing_it_as_neutral(tmp_path, clear_index):
    store = FeedbackStore(tmp_path / "clear.sqlite3")
    training = _training_result(tmp_path, count=2)
    store.save_analysis(training)
    favorite, rejected = training.candidates
    store.record_feedback(favorite, "FAVORITE")
    store.record_feedback(rejected, "REJECT")
    assert [(winner.id, loser.id) for winner, loser in store.training_pairs()] == [(favorite.id, rejected.id)]
    store.record_feedback(training.candidates[clear_index], "CLEAR")
    assert store.training_pairs() == []
    assert store.counts()["feedback"] == 3


def _store_old_ab_pairs(store: FeedbackStore, directory: Path, count: int = 805) -> None:
    video = VideoInfo("archive", str(directory / "archive.mp4"), count * 2.0, 32, 24, 30.0, "test")
    shot = Shot("archive-shot", video.id, 0, 0.0, video.duration)
    candidates = [
        Candidate(
            id=f"archive-pair-{pair}-{side}", video_id=video.id, shot_id=shot.id,
            shot_index=0, timestamp=pair * 2 + side * 0.5,
            preview_path=str(directory / "unused.png"),
            labels=["Other"], scores={**_base_scores(), "color_harmony": (0.1, 0.9)[side]},
        )
        for pair in range(count) for side in range(2)
    ]
    store.save_analysis(AnalysisResult(video, [shot], candidates, str(directory)))
    for index in range(0, len(candidates), 2):
        low, high = candidates[index:index + 2]
        store.record_preference(low, high, high)


@pytest.mark.parametrize("signal, same_video", [("ab", False), ("decisions", False), ("decisions", True)])
def test_more_than_800_old_pairs_cannot_starve_new_choices(tmp_path, signal, same_video):
    store = FeedbackStore(tmp_path / "long-history.sqlite3")
    _store_old_ab_pairs(store, tmp_path)
    recent = _training_result(tmp_path, video_id="archive" if same_video else "training")
    store.save_analysis(recent)
    _record_direction(store, recent, False, signal)

    pairs = store.training_pairs()
    identifiers = [(winner.id, loser.id) for winner, loser in pairs]
    new_direction = (recent.candidates[0].id, recent.candidates[2].id)
    assert len(pairs) == 800
    assert new_direction in identifiers[:10]
    assert len({tuple(sorted(pair)) for pair in identifiers}) == len(pairs)
    assert store.counts()["preferences"] == 805 + (1 if signal == "ab" else 0)
    assert store.training_pairs(limit=0) == []


def test_multiple_new_videos_receive_samples_before_one_old_video_fills_budget(tmp_path):
    store = FeedbackStore(tmp_path / "balanced.sqlite3")
    _store_old_ab_pairs(store, tmp_path)
    new_videos = {f"recent-{index}" for index in range(6)}
    for video_id in sorted(new_videos):
        result = _training_result(tmp_path, video_id=video_id)
        store.save_analysis(result)
        _record_direction(store, result, False, "decisions")
    pairs = store.training_pairs()
    assert new_videos <= {winner.video_id for winner, _ in pairs[:8]}


def test_newer_labels_resolve_conflicting_old_ab_without_opposite_duplicates(tmp_path):
    store = FeedbackStore(tmp_path / "channels.sqlite3")
    training = _training_result(tmp_path, count=2)
    store.save_analysis(training)
    low, high = training.candidates
    store.record_preference(low, high, high)
    store.record_feedback(low, "FAVORITE")
    store.record_feedback(high, "REJECT")
    with store._connect() as connection:
        connection.execute("UPDATE preferences SET created_at='2020-01-01 00:00:00'")
        connection.execute("UPDATE feedback SET created_at='2020-01-01 00:00:01'")
    assert [(winner.id, loser.id) for winner, loser in store.training_pairs()] == [(low.id, high.id)]
    assert len(store.preference_pairs()) == 1


def test_same_second_channel_conflict_favors_explicit_ab_and_clear_does_not_erase_ab(tmp_path):
    store = FeedbackStore(tmp_path / "same-second.sqlite3")
    training = _training_result(tmp_path, count=2)
    store.save_analysis(training)
    low, high = training.candidates
    store.record_feedback(low, "FAVORITE")
    store.record_feedback(high, "REJECT")
    store.record_preference(low, high, high)
    with store._connect() as connection:
        connection.execute("UPDATE preferences SET created_at='2020-01-01 00:00:00'")
        connection.execute("UPDATE feedback SET created_at='2020-01-01 00:00:00'")
    assert [(winner.id, loser.id) for winner, loser in store.training_pairs()] == [(high.id, low.id)]
    store.record_feedback(low, "CLEAR")
    assert [(winner.id, loser.id) for winner, loser in store.training_pairs()] == [(high.id, low.id)]


def test_changed_mode_sampling_preserves_old_payloads_feedback_and_legacy_ids(tmp_path, monkeypatch, measured_pipeline):
    store = FeedbackStore(tmp_path / "sampling.sqlite3")
    directory = tmp_path / "same-cache"
    first = measured_pipeline(directory, store)
    ordered = sorted(first.candidates, key=lambda item: item.timestamp)
    legacy = Candidate.from_dict(ordered[1].to_dict())
    legacy.id = "next-shot-original-f0001"
    first.candidates.append(legacy)
    store.save_analysis(first)
    store.record_feedback(ordered[0], "FAVORITE")
    store.record_feedback(ordered[2], "REJECT")
    store.record_feedback(legacy, "KEEP")
    previous_feedback = store.latest_feedback()
    with store._connect() as connection:
        old_payloads = dict(connection.execute("SELECT id, payload_json FROM candidates"))

    # Action sampling sends different times at the very same local indices.
    monkeypatch.setattr(pipeline, "candidate_timestamps", lambda *args: [0.6, 1.6, 2.6])
    second = measured_pipeline(directory, store, AnalysisConfig.for_mode("Action"))
    assert {item.id for item in second.candidates}.isdisjoint(old_payloads)
    assert all("-v2-" in item.id for item in second.candidates)
    with store._connect() as connection:
        new_payloads = dict(connection.execute("SELECT id, payload_json FROM candidates"))
    assert all(new_payloads[identifier] == payload for identifier, payload in old_payloads.items())
    assert store.latest_feedback() == previous_feedback
    assert store.training_pairs()  # Existing decisions still train the local model.
    assert all(Path(item.preview_path).is_file() for item in ordered)
    assert all(json.loads(old_payloads[item.id])["timestamp"] == item.timestamp for item in ordered)


def test_candidate_ids_use_decoder_precision_and_stay_stable_when_indices_move(tmp_path, monkeypatch, measured_pipeline):
    directory = tmp_path / "stable-cache"
    first = measured_pipeline(directory, None)
    original = {item.timestamp: item.id for item in first.candidates}
    monkeypatch.setattr(pipeline, "candidate_timestamps", lambda *args: [1.50000004, 0.50000004, 2.50000004])
    reordered = measured_pipeline(directory, None, AnalysisConfig.for_mode("Action"))
    assert {item.timestamp: item.id for item in reordered.candidates} == original

    monkeypatch.setattr(pipeline, "candidate_timestamps", lambda *args: [0.5000006, 1.5, 2.5])
    shifted = measured_pipeline(directory, None)
    by_time = {item.timestamp: item.id for item in shifted.candidates}
    assert "-t0p500001-" in by_time[0.500001]
    assert by_time[0.500001] != original[0.5]
    assert by_time[1.5] == original[1.5]


def test_preview_width_aspect_and_actual_crop_layout_isolate_candidate_identity(tmp_path, monkeypatch, measured_pipeline):
    directory = tmp_path / "geometry-cache"
    first = measured_pipeline(directory, None)
    original_ids = {item.id for item in first.candidates}
    narrower = measured_pipeline(directory, None, AnalysisConfig(preview_width=480))
    assert original_ids.isdisjoint(item.id for item in narrower.candidates)

    monkeypatch.setattr(pipeline, "smart_crop_to_aspect", lambda image, ratio: (
        image[:, :24].copy(), [0.0, 0.0, 0.75, 1.0]
    ))
    left = measured_pipeline(directory, None, AnalysisConfig(aspect_ratio="1:1"))
    left_ids = {item.id for item in left.candidates}
    assert original_ids.isdisjoint(left_ids)
    monkeypatch.setattr(pipeline, "smart_crop_to_aspect", lambda image, ratio: (
        image[:, 8:].copy(), [0.25, 0.0, 0.75, 1.0]
    ))
    right = measured_pipeline(directory, None, AnalysisConfig(aspect_ratio="1:1"))
    assert left_ids.isdisjoint(item.id for item in right.candidates)
    assert all(Path(item.preview_path).is_file() for item in first.candidates + left.candidates)
