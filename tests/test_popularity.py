from pathlib import Path

import cv2
import numpy as np

from framepick.models import Candidate
from framepick.popularity import IntrinsicPopularityScorer, default_model_path, normalize_popularity_scores


def _candidate(identifier: str, raw: float) -> Candidate:
    return Candidate(
        id=identifier,
        video_id="video",
        shot_id="shot",
        shot_index=0,
        timestamp=0.0,
        preview_path="/tmp/unused.jpg",
        scores={"technical": 0.8, "social_popularity_raw": raw},
    )


def test_popularity_normalization_is_ranked_and_tie_aware():
    low = _candidate("low", 1.0)
    tied_a = _candidate("tied-a", 2.0)
    tied_b = _candidate("tied-b", 2.0)
    high = _candidate("high", 4.0)
    assert normalize_popularity_scores([high, tied_b, low, tied_a]) == 4
    assert low.scores["social_popularity"] == 0.0
    assert tied_a.scores["social_popularity"] == tied_b.scores["social_popularity"] == 0.5
    assert high.scores["social_popularity"] == 1.0


def test_packaged_popularity_model_runs_in_opencv(tmp_path):
    assert default_model_path().is_file()
    image_path = tmp_path / "pattern.jpg"
    image = np.zeros((224, 224, 3), dtype=np.uint8)
    cv2.circle(image, (112, 112), 70, (50, 180, 240), -1)
    assert cv2.imwrite(str(image_path), image)
    value = IntrinsicPopularityScorer().score_path(image_path)
    assert value is not None
    assert np.isfinite(value)
