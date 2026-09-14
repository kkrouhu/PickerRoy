from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .models import CATEGORIES, Candidate


BASE_FEATURES = (
    "technical",
    "sharpness",
    "exposure",
    "contrast",
    "visual_balance",
    "rule_of_thirds",
    "temporal_peak",
    "face_quality",
    "social_popularity",
    "motion",
)
FEATURE_NAMES = BASE_FEATURES + tuple(f"category_{name.lower()}" for name in CATEGORIES[:-1])


def candidate_features(candidate: Candidate) -> np.ndarray:
    values = [float(candidate.scores.get(name, 0.0)) for name in BASE_FEATURES]
    values.extend(1.0 if category in candidate.labels else 0.0 for category in CATEGORIES[:-1])
    return np.asarray(values, dtype=np.float64)


@dataclass(frozen=True, slots=True)
class PreferenceModel:
    weights: np.ndarray
    sample_count: int

    def raw_score(self, candidate: Candidate) -> float:
        return float(candidate_features(candidate) @ self.weights)


def train_preference_model(pairs: list[tuple[Candidate, Candidate]]) -> PreferenceModel | None:
    """Fit a small regularized Bradley-Terry model from local winner/loser choices."""
    if not pairs:
        return None
    differences = np.stack([candidate_features(winner) - candidate_features(loser) for winner, loser in pairs])
    design = np.concatenate([differences, -differences], axis=0)
    labels = np.concatenate([np.ones(len(pairs)), np.zeros(len(pairs))])
    weights = np.zeros(design.shape[1], dtype=np.float64)
    regularization = 0.40
    for step in range(320):
        logits = np.clip(design @ weights, -24, 24)
        predicted = 1.0 / (1.0 + np.exp(-logits))
        gradient = design.T @ (predicted - labels) / len(labels) + regularization * weights
        learning_rate = 0.55 / (1.0 + step / 180)
        weights -= learning_rate * gradient
    return PreferenceModel(weights=weights, sample_count=len(pairs))


def apply_preference_scores(candidates: list[Candidate], model: PreferenceModel | None) -> int:
    if model is None:
        return 0
    valid = [item for item in candidates if not item.rejected]
    if not valid:
        return 0
    raw = np.asarray([model.raw_score(item) for item in valid])
    normalized = np.full(len(valid), 0.5, dtype=np.float64)
    if len(valid) > 1:
        order = np.argsort(raw, kind="stable")
        left = 0
        while left < len(order):
            right = left + 1
            while right < len(order) and abs(float(raw[order[right]]) - float(raw[order[left]])) < 1e-8:
                right += 1
            average_rank = (left + right - 1) / 2
            normalized[order[left:right]] = average_rank / (len(valid) - 1)
            left = right
    for index, item in enumerate(valid):
        item.scores["personal_preference_raw"] = round(float(raw[index]), 6)
        item.scores["personal_preference"] = round(float(normalized[index]), 5)
        item.scores["personal_preference_samples"] = float(model.sample_count)
    return len(valid)


def preference_blend_weight(sample_count: float) -> float:
    if sample_count <= 0:
        return 0.0
    return float(min(0.16, 0.04 + 0.02 * math.log2(sample_count + 1.0)))
