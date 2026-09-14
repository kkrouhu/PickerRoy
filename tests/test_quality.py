import cv2
import numpy as np

from framepick.quality import hamming_distance, perceptual_hash, technical_metrics, temporal_motion_series


def test_black_frame_is_rejected():
    image = np.zeros((240, 320, 3), dtype=np.uint8)
    scores, reasons = technical_metrics(image)
    assert "mostly_black" in reasons
    assert scores["technical"] < 0.35


def test_textured_well_exposed_frame_scores_higher_than_black():
    image = np.zeros((240, 320, 3), dtype=np.uint8)
    for y in range(0, 240, 12):
        cv2.line(image, (0, y), (319, y), (80 + y % 130,) * 3, 2)
    cv2.circle(image, (160, 120), 58, (235, 180, 70), -1)
    textured, _ = technical_metrics(image)
    black, _ = technical_metrics(np.zeros_like(image))
    assert textured["technical"] > black["technical"]


def test_perceptual_hash_is_stable_for_small_brightness_change():
    image = np.zeros((128, 128, 3), dtype=np.uint8)
    cv2.rectangle(image, (20, 20), (100, 100), (180, 120, 60), -1)
    brighter = cv2.convertScaleAbs(image, alpha=1.0, beta=8)
    assert hamming_distance(perceptual_hash(image), perceptual_hash(brighter)) <= 5


def test_temporal_motion_distinguishes_static_and_changed_frames():
    still = np.zeros((120, 160, 3), dtype=np.uint8)
    changed = still.copy()
    changed[:, 80:] = 255
    static_values = temporal_motion_series([still, still, still])
    changed_values = temporal_motion_series([still, changed, changed])
    assert max(static_values) == 0
    assert max(changed_values) > 0.5
