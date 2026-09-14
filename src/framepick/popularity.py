from __future__ import annotations

import logging
import math
import os
from pathlib import Path

import cv2
import numpy as np

from .models import Candidate
from .resources import resource_path
from .control import AnalysisControl

LOGGER = logging.getLogger(__name__)


def default_model_path() -> Path:
    override = os.environ.get("PICKERROY_POPULARITY_MODEL")
    if override:
        return Path(override).expanduser().resolve()
    return resource_path("models/intrinsic_popularity_resnet50.onnx")


class IntrinsicPopularityScorer:
    """Offline visual-popularity scorer exported from the IIPA ResNet-50 model."""

    name = "IIPA ResNet-50 (Instagram)"

    def __init__(self, model_path: str | Path | None = None) -> None:
        self.model_path = Path(model_path) if model_path else default_model_path()
        self._net: cv2.dnn.Net | None = None
        self._failed = False

    @property
    def available(self) -> bool:
        return self.model_path.is_file() and not self._failed

    def _load(self) -> cv2.dnn.Net | None:
        if self._failed:
            return None
        if self._net is not None:
            return self._net
        if not self.model_path.is_file():
            LOGGER.warning("社交媒体热度模型不存在，将继续使用基础排序：%s", self.model_path)
            self._failed = True
            return None
        try:
            self._net = cv2.dnn.readNetFromONNX(str(self.model_path))
            LOGGER.info("热门视觉模型：%s", self.name)
            return self._net
        except Exception as exc:
            LOGGER.warning("热门视觉模型加载失败，将继续使用基础排序：%s", exc)
            self._failed = True
            return None

    def score_path(self, image_path: str | Path) -> float | None:
        net = self._load()
        if net is None:
            return None
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None or image.size == 0:
            return None
        # This deliberately matches the upstream inference: RGB, 224x224 and 0..1,
        # without ImageNet mean/std normalization.
        blob = cv2.dnn.blobFromImage(image, 1.0 / 255.0, (224, 224), swapRB=True, crop=False)
        net.setInput(blob)
        value = float(net.forward().reshape(-1)[0])
        return value if math.isfinite(value) else None


def normalize_popularity_scores(candidates: list[Candidate]) -> int:
    """Convert raw model outputs into tie-aware ranks within the current video."""
    valid = [
        item for item in candidates
        if not item.rejected and math.isfinite(float(item.scores.get("social_popularity_raw", math.nan)))
    ]
    if not valid:
        return 0
    ordered = sorted(valid, key=lambda item: float(item.scores["social_popularity_raw"]))
    denominator = max(len(ordered) - 1, 1)
    index = 0
    while index < len(ordered):
        right = index + 1
        value = float(ordered[index].scores["social_popularity_raw"])
        while right < len(ordered) and abs(float(ordered[right].scores["social_popularity_raw"]) - value) < 1e-8:
            right += 1
        average_rank = (index + right - 1) / 2
        normalized = 0.5 if len(ordered) == 1 else average_rank / denominator
        for item in ordered[index:right]:
            item.scores["social_popularity"] = round(float(np.clip(normalized, 0, 1)), 5)
        index = right
    return len(valid)


def apply_popularity_scores(candidates: list[Candidate], scorer: IntrinsicPopularityScorer,
                            control: AnalysisControl | None = None) -> int:
    measured = 0
    for item in candidates:
        if control:
            control.checkpoint()
        if item.rejected or not Path(item.preview_path).is_file():
            continue
        try:
            raw = scorer.score_path(item.preview_path)
        except Exception as exc:
            LOGGER.warning("热门视觉评分失败，画面 %s 将使用基础排序：%s", item.id, exc)
            continue
        if raw is not None:
            item.scores["social_popularity_raw"] = round(raw, 6)
            measured += 1
    normalize_popularity_scores(candidates)
    return measured
