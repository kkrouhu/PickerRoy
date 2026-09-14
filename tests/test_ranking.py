from framepick.models import Candidate
from framepick.ranking import apply_temporal_peaks, diversity_rank, mark_duplicates, score_candidates


def candidate(identifier, timestamp, labels, score, hash64, shot="shot-1"):
    return Candidate(
        id=identifier,
        video_id="video",
        shot_id=shot,
        shot_index=0,
        timestamp=timestamp,
        preview_path="/tmp/unused.jpg",
        labels=labels,
        label_confidence={name: 0.8 for name in labels},
        scores={
            "technical": score,
            "sharpness": score,
            "exposure": 0.8,
            "visual_balance": 0.75,
            "rule_of_thirds": 0.7,
            "contrast": 0.7,
            "edge_density": 0.1,
            "motion": 0.5,
            "face_quality": 0.75,
        },
        hash64=hash64,
    )


def test_temporal_peak_favors_local_maximum():
    items = [candidate(str(i), i, ["Action"], value, f"{i:016x}") for i, value in enumerate([0.4, 0.6, 0.92, 0.7, 0.5])]
    apply_temporal_peaks(items)
    assert items[2].scores["temporal_peak"] > items[1].scores["temporal_peak"]


def test_dedup_keeps_higher_scoring_candidate():
    high = candidate("high", 1.0, ["Person"], 0.9, "aaaaaaaaaaaaaaaa")
    low = candidate("low", 1.1, ["Person"], 0.5, "aaaaaaaaaaaaaaaa")
    apply_temporal_peaks([high, low])
    score_candidates([high, low], "Balanced")
    kept = mark_duplicates([low, high])
    assert high in kept
    assert low.duplicate_of == high.id


def test_diversity_ranking_includes_multiple_categories():
    items = [
        candidate("p1", 1, ["Person"], 0.95, "0000000000000000", "a"),
        candidate("p2", 2, ["Person"], 0.94, "1111111111111111", "b"),
        candidate("land", 3, ["Landscape"], 0.86, "ffffffffffffffff", "c"),
    ]
    apply_temporal_peaks(items)
    score_candidates(items, "Balanced")
    ranked = diversity_rank(items, limit=3)
    assert {label for item in ranked for label in item.labels} >= {"Person", "Landscape"}

