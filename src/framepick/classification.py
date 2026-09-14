from __future__ import annotations

import logging
import platform
from pathlib import Path

import cv2
import numpy as np

from .models import CATEGORIES

LOGGER = logging.getLogger(__name__)


CATEGORY_KEYWORDS = {
    "Person": {"person", "people", "human", "face", "portrait", "man", "woman", "boy", "girl", "baby", "selfie"},
    "Action": {"sport", "running", "cycling", "ski", "skate", "jump", "dance", "swim", "climb", "exercise", "athlete", "motion"},
    "Landscape": {"landscape", "mountain", "sky", "sea", "ocean", "beach", "forest", "nature", "field", "lake", "river", "sunset", "cityscape", "outdoor"},
    "Animal": {"animal", "dog", "cat", "bird", "horse", "wildlife", "pet", "fish", "mammal", "insect"},
    "Product": {"product", "equipment", "device", "camera", "phone", "vehicle", "car", "bicycle", "food", "tool", "furniture", "shoe", "bottle"},
    "Detail": {"close-up", "closeup", "macro", "texture", "detail", "pattern", "flower", "food"},
}


class AppleVisionClassifier:
    name = "apple-vision"

    def __init__(self) -> None:
        from Foundation import NSURL  # type: ignore
        from Vision import VNClassifyImageRequest, VNDetectFaceRectanglesRequest, VNImageRequestHandler  # type: ignore

        self.NSURL = NSURL
        self.VNClassifyImageRequest = VNClassifyImageRequest
        self.VNDetectFaceRectanglesRequest = VNDetectFaceRectanglesRequest
        self.VNImageRequestHandler = VNImageRequestHandler

    def classify(self, path: str | Path) -> tuple[list[dict[str, float | str]], int]:
        url = self.NSURL.fileURLWithPath_(str(Path(path).resolve()))
        request = self.VNClassifyImageRequest.alloc().init()
        face_request = self.VNDetectFaceRectanglesRequest.alloc().init()
        handler = self.VNImageRequestHandler.alloc().initWithURL_options_(url, {})
        result = handler.performRequests_error_([request, face_request], None)
        success = result[0] if isinstance(result, tuple) else result
        if not success:
            raise RuntimeError(f"Vision request failed: {result}")
        labels = [
            {"label": str(observation.identifier()), "confidence": float(observation.confidence())}
            for observation in (request.results() or [])[:20]
        ]
        return labels, len(face_request.results() or [])


class HeuristicClassifier:
    name = "opencv-fallback"

    def __init__(self) -> None:
        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        self.face_detector = cv2.CascadeClassifier(str(cascade_path))

    def classify(self, path: str | Path) -> tuple[list[dict[str, float | str]], int]:
        image = cv2.imread(str(path))
        if image is None:
            return [], 0
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.face_detector.detectMultiScale(gray, scaleFactor=1.12, minNeighbors=5, minSize=(32, 32))
        labels: list[dict[str, float | str]] = []
        if len(faces):
            labels.append({"label": "person", "confidence": min(0.95, 0.62 + len(faces) * 0.08)})
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        green = float(np.mean((hsv[:, :, 0] > 30) & (hsv[:, :, 0] < 95) & (hsv[:, :, 1] > 45)))
        blue = float(np.mean((hsv[:, :, 0] > 90) & (hsv[:, :, 0] < 135) & (hsv[:, :, 1] > 35)))
        if green + blue > 0.28:
            labels.append({"label": "landscape nature outdoor", "confidence": min(0.70, 0.38 + green + blue)})
        return labels, len(faces)


class ResilientClassifier:
    """Use a platform backend when it works, then permanently fall back after a runtime failure."""

    name = "resilient-local"

    def __init__(self, primary, fallback):
        self.primary = primary
        self.fallback = fallback
        self._primary_enabled = primary is not None

    @property
    def active_name(self) -> str:
        return self.primary.name if self._primary_enabled else self.fallback.name

    def classify(self, path: str | Path) -> tuple[list[dict[str, float | str]], int]:
        if self._primary_enabled:
            try:
                return self.primary.classify(path)
            except Exception as exc:
                self._primary_enabled = False
                LOGGER.warning("Content backend %s failed at runtime; switching to %s: %s", self.primary.name, self.fallback.name, exc)
        return self.fallback.classify(path)


def build_classifier():
    fallback = HeuristicClassifier()
    if platform.system() == "Darwin":
        try:
            backend = AppleVisionClassifier()
            LOGGER.info("Content classifier: Apple Vision")
            return ResilientClassifier(backend, fallback)
        except Exception as exc:
            LOGGER.warning("Apple Vision unavailable, using CPU fallback: %s", exc)
    return ResilientClassifier(None, fallback)


def categories_from_observations(observations: list[dict[str, float | str]], face_count: int,
                                 motion: float, edge_density: float, aspect_ratio: float) -> tuple[list[str], dict[str, float]]:
    confidence = {name: 0.0 for name in CATEGORIES}
    for row in observations:
        label = str(row.get("label", "")).lower()
        score = float(row.get("confidence", 0.0))
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(keyword in label for keyword in keywords):
                confidence[category] = max(confidence[category], score)
    if face_count:
        confidence["Person"] = max(confidence["Person"], min(0.98, 0.70 + face_count * 0.06))
    if motion > 0.48 and (face_count or confidence["Animal"] > 0.12 or confidence["Product"] > 0.22):
        confidence["Action"] = max(confidence["Action"], 0.42 + 0.45 * motion)
    if aspect_ratio > 1.25 and face_count == 0 and edge_density > 0.035:
        confidence["Landscape"] = max(confidence["Landscape"], 0.26)
    if edge_density > 0.16 and face_count == 0:
        confidence["Detail"] = max(confidence["Detail"], min(0.65, edge_density * 2.6))
    labels = [name for name in CATEGORIES[:-1] if confidence[name] >= 0.24]
    if not labels:
        labels = ["Other"]
        confidence["Other"] = 0.5
    return labels, {name: round(score, 5) for name, score in confidence.items() if score > 0}


def face_region_sharpness(image: np.ndarray, face_count: int) -> float:
    if not face_count:
        return 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # A conservative proxy when Vision reports faces; detailed landmarks are a later-round backend.
    center = gray[gray.shape[0] // 5: gray.shape[0] * 4 // 5, gray.shape[1] // 5: gray.shape[1] * 4 // 5]
    value = float(cv2.Laplacian(center, cv2.CV_64F).var()) if center.size else 0.0
    return float(np.clip(np.log1p(value) / 7.0, 0, 1))
