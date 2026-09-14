from framepick.models import Candidate
from framepick.preference import apply_preference_scores, train_preference_model


def _candidate(identifier: str, sharpness: float) -> Candidate:
    return Candidate(
        id=identifier,
        video_id="video",
        shot_id="shot",
        shot_index=0,
        timestamp=0.0,
        preview_path="unused.jpg",
        labels=["Person"],
        scores={
            "technical": 0.75,
            "sharpness": sharpness,
            "exposure": 0.7,
            "contrast": 0.6,
            "visual_balance": 0.7,
            "rule_of_thirds": 0.6,
            "temporal_peak": 0.5,
            "face_quality": sharpness,
            "social_popularity": 0.5,
            "motion": 0.2,
        },
    )


def test_pairwise_choices_train_a_local_preference_score():
    preferred = _candidate("preferred", 0.95)
    rejected = _candidate("rejected", 0.25)
    model = train_preference_model([(preferred, rejected)] * 5)
    assert model is not None
    assert model.raw_score(preferred) > model.raw_score(rejected)
    assert apply_preference_scores([rejected, preferred], model) == 2
    assert preferred.scores["personal_preference"] == 1.0
    assert rejected.scores["personal_preference"] == 0.0
    assert preferred.scores["personal_preference_samples"] == 5.0
