from __future__ import annotations

import math

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
