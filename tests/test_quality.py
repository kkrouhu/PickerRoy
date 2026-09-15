import cv2
import numpy as np
import pytest

from framepick.quality import (
    aesthetic_metrics,
    enhancement_diagnostics,
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


def test_enhancement_keeps_pixel_dimensions_and_source_untouched():
    image = np.full((900, 600, 3), 120, dtype=np.uint8)
    original = image.copy()
    enhanced = optimized_export_image(image, 3840, 2160)
    assert enhanced.shape == image.shape
    assert enhanced.dtype == np.uint8
    np.testing.assert_array_equal(image, original)
    # Legacy callers may still supply scaling arguments: none resample pixels.
    assert optimized_export_image(image, 9999, 9999, max_scale=4, max_megapixels=0.1).shape == image.shape


@pytest.mark.parametrize("color", [(0, 0, 0), (255, 255, 255), (127, 127, 127), (10, 40, 70)])
def test_enhancement_does_not_invent_detail_in_uniform_frames(color):
    image = np.full((48, 64, 3), color, dtype=np.uint8)
    settings = enhancement_diagnostics(image)
    assert settings["protected_frame"]
    assert settings["sharpen_amount"] == 0
    np.testing.assert_array_equal(optimized_export_image(image, 64, 48), image)


def test_flat_gray_tones_gain_contrast_without_chroma_or_clipping():
    gray = np.tile(np.linspace(88, 162, 320).astype(np.uint8), (180, 1))
    image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    output = optimized_export_image(image, 320, 180)
    settings = enhancement_diagnostics(image)
    assert settings["contrast_strength"] > 0.10
    assert output[:, :, 0].std() > gray.std() * 1.10
    assert np.diff(output[90, :, 0].astype(int)).min() >= 0
    np.testing.assert_array_equal(output[:, :, 0], output[:, :, 1])
    np.testing.assert_array_equal(output[:, :, 1], output[:, :, 2])
    assert output.min() > 0 and output.max() < 255


def test_limited_shadow_lift_preserves_true_black_and_white():
    gray = np.tile(np.linspace(0, 110, 320).astype(np.uint8), (180, 1))
    image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    image[0:4] = 255
    output = optimized_export_image(image, 320, 180)
    assert enhancement_diagnostics(image)["shadow_lift"] > 0
    assert output[90, 130:200, 0].mean() > image[90, 130:200, 0].mean()
    np.testing.assert_array_equal(output[0:4], image[0:4])
    np.testing.assert_array_equal(output[10:, 0], image[10:, 0])
    assert output[90].max() < 140  # Low-key lighting must not become a daytime exposure.


def test_bright_background_does_not_veto_recoverable_foreground_shadows():
    image = np.full((360, 480, 3), (245, 230, 218), np.uint8)
    ramp = np.tile(np.linspace(22, 62, 480).astype(np.uint8), (115, 1))
    image[245:] = cv2.cvtColor(ramp, cv2.COLOR_GRAY2BGR)
    image[-1, :4] = 0
    settings = enhancement_diagnostics(image)
    assert settings["median_luma"] > 0.8
    assert settings["dynamic_range"] > 0.7
    assert settings["contrast_strength"] == 0
    assert settings["shadow_lift"] > 0.035
    output = optimized_export_image(image, 480, 360)
    assert output[260:355].mean() > image[260:355].mean() + 7
    # Opening shade must not lift the entire scene or introduce clipped pixels.
    assert np.abs(output[:220].astype(int) - image[:220].astype(int)).mean() < 2
    np.testing.assert_array_equal(output[-1, :4], image[-1, :4])
    assert not np.any((output == 255) & (image < 255))
    assert not np.any((output == 0) & (image > 0))


def test_shadow_lift_does_not_wash_existing_color_out_with_additive_white():
    image = np.full((360, 480, 3), 225, np.uint8)
    shade = np.tile(np.linspace(25, 58, 480).astype(np.uint8), (120, 1))
    image[240:, :, 0] = shade
    image[240:, :, 1] = (shade * 1.25).astype(np.uint8)
    image[240:, :, 2] = (shade * 0.75).astype(np.uint8)
    output = optimized_export_image(image, 480, 360)
    before_sat = cv2.cvtColor(image[250:], cv2.COLOR_BGR2HSV)[:, :, 1].mean()
    after_sat = cv2.cvtColor(output[250:], cv2.COLOR_BGR2HSV)[:, :, 1].mean()
    assert output[250:].mean() > image[250:].mean() + 5
    assert before_sat - 2 <= after_sat <= before_sat * 1.20


def test_high_saturation_already_rich_frame_gets_no_saturation_push():
    hue = np.tile(np.linspace(0, 179, 320).astype(np.uint8), (180, 1))
    hsv = np.stack([hue, np.full_like(hue, 230), np.tile(np.linspace(20, 250, 180).astype(np.uint8)[:, None], (1, 320))], axis=2)
    image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    assert enhancement_diagnostics(image)["saturation_strength"] == 0
    output = optimized_export_image(image, 320, 180)
    assert np.mean(cv2.cvtColor(output, cv2.COLOR_BGR2HSV)[:, :, 1]) <= np.mean(hsv[:, :, 1]) + 2
    assert float((output == 255).mean()) <= float((image == 255).mean())


def test_noise_only_frame_is_not_sharpened_or_amplified():
    rng = np.random.default_rng(492)
    image = np.clip(rng.normal(90, 12, (256, 320, 3)), 0, 255).astype(np.uint8)
    settings = enhancement_diagnostics(image)
    assert settings["noise_sigma"] > 6
    assert settings["sharpen_amount"] == 0
    assert settings["reason"] == "noise_without_structure"
    np.testing.assert_array_equal(optimized_export_image(image, 320, 256), image)


def test_already_crisp_contours_have_no_sharpening_or_edge_halos():
    gray = np.tile(np.where(np.arange(320) % 40 < 20, 45, 210).astype(np.uint8), (180, 1))
    image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    assert enhancement_diagnostics(image)["sharpen_amount"] == 0
    output = optimized_export_image(image, 320, 180)
    assert np.unique(output[:, :, 0]).size == 2


def test_only_clean_slightly_soft_structure_is_eligible_for_tiny_sharpening():
    image = np.full((320, 480, 3), 90, np.uint8)
    cv2.rectangle(image, (240, 40), (450, 250), (100, 150, 200), -1)
    for y in range(30, 300, 50):
        cv2.circle(image, (50 + y, y), 20, (180, 120, 100), -1)
    mild = cv2.GaussianBlur(image, (0, 0), 1.5)
    assert 0 < enhancement_diagnostics(mild)["sharpen_amount"] <= 0.06
    severe = cv2.GaussianBlur(image, (0, 0), 5.0)
    assert enhancement_diagnostics(severe)["sharpen_amount"] == 0
    noise = np.random.default_rng(327).normal(0, 6, mild.shape)
    noisy = np.clip(mild.astype(float) + noise, 0, 255).astype(np.uint8)
    assert enhancement_diagnostics(noisy)["sharpen_amount"] == 0


def test_low_saturation_gains_color_with_warm_hues_protected():
    hsv = np.zeros((180, 320, 3), np.uint8)
    hsv[:, :, 0] = 100
    hsv[:, :, 1] = 60
    hsv[:, :, 2] = np.tile(np.linspace(80, 190, 320).astype(np.uint8), (180, 1))
    image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    output = optimized_export_image(image, 320, 180)
    before_sat = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)[:, :, 1].mean()
    after_sat = cv2.cvtColor(output, cv2.COLOR_BGR2HSV)[:, :, 1].mean()
    assert before_sat + 2 < after_sat < before_sat * 1.20
    # Same low-saturation brightness ramp, but in the conservatively protected
    # warm hue range. The existing hue must not drift as color is adjusted.
    hsv[:, :, 0] = 12
    warm = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    warm_output = optimized_export_image(warm, 320, 180)
    warm_hsv = cv2.cvtColor(warm_output, cv2.COLOR_BGR2HSV)
    assert np.abs(warm_hsv[:, :, 0].astype(int) - 12).max() <= 2
    assert np.mean(warm_hsv[:, :, 1]) < after_sat


def test_mid_saturation_enhancement_survives_eight_bit_quantization():
    hsv = np.zeros((180, 320, 3), np.uint8)
    hsv[:, :, 0] = 100
    hsv[:, :, 1] = 90
    hsv[:, :, 2] = np.tile(np.linspace(128, 240, 320).astype(np.uint8), (180, 1))
    image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    output = optimized_export_image(image, 320, 180)
    before_sat = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)[:, :, 1].mean()
    after_sat = cv2.cvtColor(output, cv2.COLOR_BGR2HSV)[:, :, 1].mean()
    assert after_sat > before_sat + 3
    assert after_sat < before_sat * 1.20


def test_diagnostics_are_json_safe_and_deterministic():
    import json
    image = np.arange(48 * 64 * 3, dtype=np.uint8).reshape(48, 64, 3)
    settings = enhancement_diagnostics(image)
    assert settings == enhancement_diagnostics(image)
    assert json.loads(json.dumps(settings)) == settings
    assert 0 <= settings["sharpen_amount"] <= 0.06


def test_memory_bounded_strips_match_whole_frame_without_seams():
    from framepick.quality import _apply_enhancement
    image = np.full((640, 960, 3), 90, np.uint8)
    for y in range(30, 630, 35):
        cv2.rectangle(image, (80, y), (870, y + 14), (110, 160, 200), -1)
    image = cv2.GaussianBlur(image, (0, 0), 1.5)
    settings = enhancement_diagnostics(image)
    assert settings["sharpen_amount"] > 0
    expected = _apply_enhancement(image, settings)
    actual = optimized_export_image(image, 960, 640)
    np.testing.assert_array_equal(actual, expected)


@pytest.mark.parametrize("image", [np.zeros((0, 0, 3), np.uint8), np.zeros((8, 8), np.uint8), np.zeros((8, 8, 3), np.float32)])
def test_enhancement_rejects_unsupported_pixel_layouts(image):
    with pytest.raises(ValueError):
        enhancement_diagnostics(image)
