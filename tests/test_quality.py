import cv2
import numpy as np
import pytest

from framepick.quality import (
    aesthetic_metrics,
    hamming_distance,
    optimized_export_image,
    perceptual_hash,
    smart_crop_to_aspect,
    technical_metrics,
    temporal_motion_series,
)


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


def test_smart_crop_produces_requested_ratios():
    image = np.zeros((600, 1000, 3), dtype=np.uint8)
    cv2.circle(image, (720, 260), 80, (255, 255, 255), -1)
    square, square_box = smart_crop_to_aspect(image, 1.0)
    portrait, portrait_box = smart_crop_to_aspect(image, 2 / 3)
    assert square.shape[:2] == (600, 600)
    assert portrait.shape[1] / portrait.shape[0] == pytest.approx(2 / 3, abs=0.01)
    assert square_box[2] < 1.0
    assert portrait_box[2] < square_box[2]


def test_theme_aesthetic_metrics_are_bounded():
    image = np.zeros((360, 640, 3), dtype=np.uint8)
    image[:180] = (210, 135, 70)
    image[180:] = (45, 125, 55)
    cv2.line(image, (0, 240), (639, 240), (245, 245, 245), 4)
    scores = aesthetic_metrics(image)
    assert 0 <= scores["landscape_aesthetic"] <= 1
    assert 0 <= scores["horizon_composition"] <= 1
    assert scores["portrait_aesthetic"] == 0


def test_optimized_export_recovers_pixels_with_safety_limits():
    image = np.full((900, 600, 3), 120, dtype=np.uint8)
    enhanced = optimized_export_image(image, 3840, 2160)
    assert enhanced.shape[0] > image.shape[0]
    assert enhanced.shape[1] > image.shape[1]
    assert enhanced.shape[0] <= image.shape[0] * 2
    assert enhanced.shape[0] * enhanced.shape[1] <= 24_000_000
