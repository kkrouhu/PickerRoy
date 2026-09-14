from __future__ import annotations

import math
from functools import lru_cache

import cv2
import numpy as np


def smart_crop_to_aspect(image: np.ndarray, target_ratio: float | None) -> tuple[np.ndarray, list[float]]:
    """Crop around a conservative edge-saliency center and return a normalized source crop box."""
    if target_ratio is None or image is None or image.size == 0:
        return image, [0.0, 0.0, 1.0, 1.0]
    height, width = image.shape[:2]
    source_ratio = width / max(height, 1)
    if abs(source_ratio - target_ratio) < 0.01:
        return image, [0.0, 0.0, 1.0, 1.0]

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 70, 160).astype(np.float32)
    edges = cv2.GaussianBlur(edges, (0, 0), sigmaX=max(3.0, min(width, height) / 35)) + 1.0
    yy, xx = np.mgrid[0:height, 0:width]
    total = float(edges.sum())
    saliency_x = float((xx * edges).sum() / total) if total else width / 2
    saliency_y = float((yy * edges).sum() / total) if total else height / 2
    # A strong center prior prevents isolated highlights near an edge from producing an unsafe crop.
    center_x = 0.62 * saliency_x + 0.38 * width / 2
    center_y = 0.62 * saliency_y + 0.38 * height / 2

    if source_ratio > target_ratio:
        crop_height = height
        crop_width = max(1, min(width, round(height * target_ratio)))
    else:
        crop_width = width
        crop_height = max(1, min(height, round(width / target_ratio)))
    left = int(np.clip(round(center_x - crop_width / 2), 0, width - crop_width))
    top = int(np.clip(round(center_y - crop_height / 2), 0, height - crop_height))
    cropped = image[top:top + crop_height, left:left + crop_width].copy()
    return cropped, [left / width, top / height, crop_width / width, crop_height / height]


def _sigmoid(value: float, center: float, scale: float) -> float:
    return 1.0 / (1.0 + math.exp(-(value - center) / max(scale, 1e-6)))


def perceptual_hash(image: np.ndarray) -> str:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA)
    dct = cv2.dct(np.float32(resized))[:8, :8]
    median = float(np.median(dct[1:, :]))
    bits = (dct > median).flatten()
    number = 0
    for bit in bits:
        number = (number << 1) | int(bit)
    return f"{number:016x}"


def hamming_distance(left: str, right: str) -> int:
    if not left or not right:
        return 64
    return (int(left, 16) ^ int(right, 16)).bit_count()


def temporal_motion_series(images: list[np.ndarray]) -> list[float]:
    """Estimate local change around each sampled moment without retaining full video frames."""
    if not images:
        return []
    grays = []
    for image in images:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape
        scale = min(1.0, 320 / max(width, 1))
        resized = cv2.resize(gray, (max(1, round(width * scale)), max(1, round(height * scale))), interpolation=cv2.INTER_AREA)
        grays.append(cv2.GaussianBlur(resized, (5, 5), 0))
    transitions = [
        float(np.clip(np.percentile(cv2.absdiff(left, right), 75) / 70.0, 0, 1))
        for left, right in zip(grays, grays[1:])
    ]
    if not transitions:
        return [0.0]
    return [
        max(transitions[max(0, index - 1):min(len(transitions), index + 1)] or [0.0])
        for index in range(len(grays))
    ]


def technical_metrics(image: np.ndarray, motion: float = 0.0) -> tuple[dict[str, float], list[str]]:
    if image is None or image.size == 0:
        return {"technical": 0.0}, ["decode_error"]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    pixels = gray.astype(np.float32)
    mean = float(pixels.mean())
    contrast = float(pixels.std())
    black_fraction = float(np.mean(pixels <= 8))
    white_fraction = float(np.mean(pixels >= 247))
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    lap_variance = float(laplacian.var())
    sharpness = _sigmoid(math.log1p(lap_variance), center=4.15, scale=0.72)

    sobel_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    edge_energy = float(np.mean(cv2.magnitude(sobel_x, sobel_y)))
    edge_density = float(np.mean(cv2.Canny(gray, 70, 160) > 0))
    directionality = abs(float(np.mean(np.abs(sobel_x))) - float(np.mean(np.abs(sobel_y))))
    directionality /= max(edge_energy, 1e-6)

    exposure_center = math.exp(-((mean - 126.0) / 86.0) ** 2)
    clipping_penalty = min(1.0, black_fraction * 1.55 + white_fraction * 1.8)
    exposure = float(np.clip(exposure_center * (1.0 - 0.72 * clipping_penalty), 0, 1))
    contrast_score = float(np.clip((contrast - 12) / 48, 0, 1))

    # Dynamic shots tolerate directional blur; low edge energy and low Laplacian remain failures.
    expressive_blur_credit = min(0.16, motion * directionality * 0.22)
    blur_score = float(np.clip(sharpness + expressive_blur_credit, 0, 1))
    technical = float(np.clip(0.46 * blur_score + 0.38 * exposure + 0.16 * contrast_score, 0, 1))
    reasons: list[str] = []
    if black_fraction > 0.80 or (mean < 12 and contrast < 15):
        reasons.append("mostly_black")
    if white_fraction > 0.72 or (mean > 245 and contrast < 12):
        reasons.append("severe_overexposure")
    if sharpness < 0.13 and edge_density < 0.035:
        reasons.append("severe_blur_or_defocus")
    if contrast < 4.5:
        reasons.append("transition_or_blank")
    return {
        "technical": technical,
        "sharpness": sharpness,
        "exposure": exposure,
        "contrast": contrast_score,
        "black_fraction": black_fraction,
        "white_fraction": white_fraction,
        "edge_density": edge_density,
        "motion": float(np.clip(motion, 0, 1)),
        "expressive_blur": expressive_blur_credit,
        "mean_luma": mean / 255.0,
        "resolution_megapixels": (width * height) / 1_000_000,
    }, reasons


def composition_metrics(image: np.ndarray) -> dict[str, float]:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 180).astype(np.float32) / 255.0
    height, width = gray.shape
    yy, xx = np.mgrid[0:height, 0:width]
    energy = edges + 0.001
    total = float(energy.sum())
    cx = float((xx * energy).sum() / total) / max(width, 1)
    cy = float((yy * energy).sum() / total) / max(height, 1)
    targets = [(1 / 3, 1 / 3), (2 / 3, 1 / 3), (1 / 3, 2 / 3), (2 / 3, 2 / 3), (0.5, 0.5)]
    distance = min(math.dist((cx, cy), target) for target in targets)
    balance = float(np.clip(1.0 - distance / 0.5, 0, 1))
    thirds = float(np.clip(1.0 - min(math.dist((cx, cy), target) for target in targets[:4]) / 0.45, 0, 1))
    return {"visual_balance": balance, "rule_of_thirds": thirds, "saliency_x": cx, "saliency_y": cy}


@lru_cache(maxsize=1)
def _portrait_detectors():
    root = cv2.data.haarcascades
    return (
        cv2.CascadeClassifier(root + "haarcascade_frontalface_default.xml"),
        cv2.CascadeClassifier(root + "haarcascade_eye_tree_eyeglasses.xml"),
        cv2.CascadeClassifier(root + "haarcascade_smile.xml"),
    )


def portrait_aesthetic_metrics(image: np.ndarray, face_count_hint: int = 0) -> dict[str, float]:
    """Theme-aware portrait cues: visible face, eye line, expression, focus and exposure."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    face_detector, eye_detector, smile_detector = _portrait_detectors()
    scale = min(1.0, 640 / max(width, 1))
    small = cv2.resize(gray, (max(1, round(width * scale)), max(1, round(height * scale))), interpolation=cv2.INTER_AREA)
    faces = face_detector.detectMultiScale(small, scaleFactor=1.12, minNeighbors=5, minSize=(30, 30))
    if not len(faces) and face_count_hint:
        faces = np.asarray([[round(small.shape[1] * 0.25), round(small.shape[0] * 0.16),
                             round(small.shape[1] * 0.50), round(small.shape[0] * 0.62)]])
    if not len(faces):
        return {
            "portrait_aesthetic": 0.0, "face_visibility": 0.0, "face_composition": 0.0,
            "eye_visibility": 0.0, "expression": 0.0, "face_exposure": 0.0,
        }

    face_scores = []
    expression_scores = []
    eye_scores = []
    for x, y, w, h in faces[:5]:
        roi = small[y:y + h, x:x + w]
        if not roi.size:
            continue
        eyes = eye_detector.detectMultiScale(roi[:max(1, round(h * 0.65))], scaleFactor=1.10, minNeighbors=5, minSize=(8, 8))
        smiles = smile_detector.detectMultiScale(roi[round(h * 0.35):], scaleFactor=1.55, minNeighbors=18, minSize=(15, 8))
        eye_score = float(np.clip(len(eyes) / 2.0, 0, 1))
        expression = 0.70 if len(smiles) else 0.46
        area = (w * h) / max(small.shape[0] * small.shape[1], 1)
        visibility = float(np.clip(area / 0.12, 0, 1))
        center = ((x + w / 2) / small.shape[1], (y + h * 0.42) / small.shape[0])
        composition = float(np.clip(1.0 - min(
            math.dist(center, target) for target in ((0.5, 0.36), (1 / 3, 1 / 3), (2 / 3, 1 / 3))
        ) / 0.48, 0, 1))
        focus = float(np.clip(np.log1p(cv2.Laplacian(roi, cv2.CV_64F).var()) / 7.2, 0, 1))
        mean = float(roi.mean())
        exposure = float(math.exp(-((mean - 132.0) / 82.0) ** 2))
        face_scores.append(0.20 * visibility + 0.22 * composition + 0.24 * focus + 0.18 * exposure + 0.10 * eye_score + 0.06 * expression)
        expression_scores.append(expression)
        eye_scores.append(eye_score)
    best = max(face_scores or [0.0])
    primary = max(faces, key=lambda row: row[2] * row[3])
    x, y, w, h = primary
    center = ((x + w / 2) / small.shape[1], (y + h * 0.42) / small.shape[0])
    face_composition = float(np.clip(1.0 - min(
        math.dist(center, target) for target in ((0.5, 0.36), (1 / 3, 1 / 3), (2 / 3, 1 / 3))
    ) / 0.48, 0, 1))
    roi = small[y:y + h, x:x + w]
    return {
        "portrait_aesthetic": float(np.clip(best, 0, 1)),
        "face_visibility": float(np.clip((w * h) / max(small.size * 0.12, 1), 0, 1)),
        "face_composition": face_composition,
        "eye_visibility": max(eye_scores or [0.0]),
        "expression": max(expression_scores or [0.0]),
        "face_exposure": float(math.exp(-((float(roi.mean()) - 132.0) / 82.0) ** 2)) if roi.size else 0.0,
    }


def landscape_aesthetic_metrics(image: np.ndarray) -> dict[str, float]:
    """Theme-aware scenic cues inspired by photographic composition research."""
    height, width = image.shape[:2]
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    saturation = hsv[:, :, 1].astype(np.float32) / 255.0
    value = hsv[:, :, 2].astype(np.float32) / 255.0
    chromatic = saturation > 0.12
    hue_hist = cv2.calcHist([hsv], [0], chromatic.astype(np.uint8), [18], [0, 180]).reshape(-1)
    hue_hist /= max(float(hue_hist.sum()), 1.0)
    entropy = -float(np.sum(hue_hist[hue_hist > 0] * np.log(hue_hist[hue_hist > 0]))) / math.log(18)
    color_harmony = float(np.clip(1.0 - abs(entropy - 0.42) / 0.58, 0, 1))
    saturation_quality = float(np.clip(1.0 - abs(float(saturation.mean()) - 0.38) / 0.38, 0, 1))
    tonal_range = float(np.clip((np.percentile(value, 95) - np.percentile(value, 5)) / 0.72, 0, 1))

    hue = hsv[:, :, 0]
    green = (hue >= 30) & (hue <= 92) & (saturation > 0.18)
    blue = (hue >= 90) & (hue <= 138) & (saturation > 0.16)
    warm = ((hue <= 25) | (hue >= 165)) & (saturation > 0.22)
    scenicness = float(np.clip((green.mean() + blue.mean() + 0.55 * warm.mean()) * 1.8, 0, 1))

    small_scale = min(1.0, 520 / max(width, 1))
    small = cv2.resize(gray, (max(1, round(width * small_scale)), max(1, round(height * small_scale))), interpolation=cv2.INTER_AREA)
    edges = cv2.Canny(small, 70, 160)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=max(24, small.shape[1] // 9),
                            minLineLength=max(30, small.shape[1] // 4), maxLineGap=max(8, small.shape[1] // 30))
    horizon = 0.45
    if lines is not None:
        candidates = []
        for x1, y1, x2, y2 in lines[:, 0]:
            angle = abs(math.degrees(math.atan2(y2 - y1, x2 - x1)))
            if angle <= 8:
                y_center = ((y1 + y2) / 2) / max(small.shape[0], 1)
                position = 1.0 - min(abs(y_center - 1 / 3), abs(y_center - 2 / 3)) / (1 / 3)
                length = math.hypot(x2 - x1, y2 - y1) / max(small.shape[1], 1)
                candidates.append(float(np.clip(0.62 * position + 0.38 * length, 0, 1)))
        if candidates:
            horizon = max(candidates)

    band_features = []
    for band in np.array_split(gray, 3, axis=0):
        band_features.append((float(band.mean()) / 255.0, float(cv2.Canny(band, 80, 170).mean()) / 255.0))
    depth_layers = float(np.clip(np.std([row[0] for row in band_features]) * 3.2 +
                                 np.std([row[1] for row in band_features]) * 2.2, 0, 1))
    score = (0.19 * color_harmony + 0.14 * saturation_quality + 0.20 * tonal_range +
             0.18 * horizon + 0.14 * depth_layers + 0.15 * scenicness)
    return {
        "landscape_aesthetic": float(np.clip(score, 0, 1)),
        "color_harmony": color_harmony,
        "saturation_quality": saturation_quality,
        "tonal_range": tonal_range,
        "horizon_composition": horizon,
        "depth_layers": depth_layers,
        "scenicness": scenicness,
    }


def aesthetic_metrics(image: np.ndarray, face_count_hint: int = 0) -> dict[str, float]:
    metrics = landscape_aesthetic_metrics(image)
    metrics.update(portrait_aesthetic_metrics(image, face_count_hint))
    metrics["aesthetic_quality"] = float(np.clip(
        0.45 * metrics["landscape_aesthetic"] + 0.55 * metrics["portrait_aesthetic"]
        if face_count_hint else metrics["landscape_aesthetic"], 0, 1
    ))
    return metrics


def optimized_export_image(image: np.ndarray, source_width: int, source_height: int,
                           max_scale: float = 2.0, max_megapixels: float = 24.0) -> np.ndarray:
    """Gently restore cropped output with pixel-area recovery, tone, color and sharpening."""
    height, width = image.shape[:2]
    source_area = max(1, source_width * source_height)
    current_area = max(1, width * height)
    scale = max(1.0, min(max_scale, math.sqrt(source_area / current_area)))
    target_area = current_area * scale * scale
    if target_area > max_megapixels * 1_000_000:
        scale *= math.sqrt((max_megapixels * 1_000_000) / target_area)
    if scale > 1.015:
        image = cv2.resize(image, (round(width * scale), round(height * scale)), interpolation=cv2.INTER_LANCZOS4)

    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.55, tileGridSize=(8, 8))
    balanced_l = clahe.apply(l_channel)
    l_channel = cv2.addWeighted(l_channel, 0.68, balanced_l, 0.32, 0)
    toned = cv2.cvtColor(cv2.merge((l_channel, a_channel, b_channel)), cv2.COLOR_LAB2BGR)

    hsv = cv2.cvtColor(toned, cv2.COLOR_BGR2HSV).astype(np.float32)
    mean_saturation = float(hsv[:, :, 1].mean())
    saturation_gain = 1.08 if mean_saturation < 150 else 1.02
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation_gain, 0, 255)
    toned = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    blurred = cv2.GaussianBlur(toned, (0, 0), 1.05)
    return cv2.addWeighted(toned, 1.34, blurred, -0.34, 0)
