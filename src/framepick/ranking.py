from __future__ import annotations

from collections import defaultdict

import numpy as np

from .models import CATEGORIES, Candidate
from .preference import preference_blend_weight
from .quality import hamming_distance


MODE_CATEGORY_BOOST = {
    "Balanced": {},
    "Portrait": {"Person": 0.16},
    "Action": {"Action": 0.18},
    "Landscape": {"Landscape": 0.18, "Plant": 0.10},
    "Product": {"Product": 0.18, "Detail": 0.06},
}

SOCIAL_POPULARITY_WEIGHT = {
    "Person": 0.22,
    "Action": 0.16,
    "Landscape": 0.20,
    "Animal": 0.18,
    "Plant": 0.19,
    "Product": 0.18,
    "Detail": 0.20,
    "Other": 0.18,
}


def category_scores(candidate: Candidate, mode: str = "Balanced") -> dict[str, float]:
    s = candidate.scores
    technical = s.get("technical", 0.0)
    sharpness = s.get("sharpness", 0.0)
    exposure = s.get("exposure", 0.0)
    composition = 0.55 * s.get("visual_balance", 0.0) + 0.45 * s.get("rule_of_thirds", 0.0)
    motion = s.get("motion", 0.0)
    temporal = s.get("temporal_peak", 0.5)
    face = s.get("face_quality", 0.0)
    category_confidence = candidate.label_confidence
    social_popularity = s.get("social_popularity", 0.5)
    values = {
        "Person": 0.28 * technical + 0.23 * face + 0.17 * sharpness + 0.13 * exposure + 0.12 * composition + 0.07 * temporal,
        "Action": 0.23 * technical + 0.17 * sharpness + 0.21 * temporal + 0.18 * motion + 0.13 * composition + 0.08 * exposure,
        "Landscape": 0.29 * technical + 0.19 * sharpness + 0.21 * composition + 0.19 * exposure + 0.12 * s.get("contrast", 0),
        "Animal": 0.27 * technical + 0.20 * sharpness + 0.18 * temporal + 0.15 * composition + 0.12 * exposure + 0.08 * motion,
        "Plant": 0.27 * technical + 0.22 * sharpness + 0.19 * composition + 0.15 * exposure + 0.11 * s.get("contrast", 0) + 0.06 * s.get("edge_density", 0),
        "Product": 0.31 * technical + 0.25 * sharpness + 0.20 * composition + 0.16 * exposure + 0.08 * s.get("contrast", 0),
        "Detail": 0.31 * technical + 0.30 * sharpness + 0.18 * composition + 0.13 * exposure + 0.08 * s.get("edge_density", 0),
        "Other": 0.48 * technical + 0.22 * composition + 0.18 * exposure + 0.12 * temporal,
    }
    boost = MODE_CATEGORY_BOOST.get(mode, {})
    for category in values:
        social_weight = SOCIAL_POPULARITY_WEIGHT[category]
        values[category] = (1.0 - social_weight) * values[category] + social_weight * social_popularity
        personal_weight = preference_blend_weight(s.get("personal_preference_samples", 0.0))
        if personal_weight:
            personal = s.get("personal_preference", 0.5)
            values[category] = (1.0 - personal_weight) * values[category] + personal_weight * personal
        semantic = category_confidence.get(category, 0.0)
        values[category] = float(np.clip(values[category] * (0.88 + 0.12 * semantic) + boost.get(category, 0), 0, 1))
    return values


def apply_temporal_peaks(candidates: list[Candidate]) -> None:
    groups: dict[str, list[Candidate]] = defaultdict(list)
    for item in candidates:
        groups[item.shot_id].append(item)
    for items in groups.values():
        items.sort(key=lambda row: row.timestamp)
        base = np.array([
            0.56 * row.scores.get("technical", 0) + 0.24 * row.scores.get("motion", 0) +
            0.20 * row.scores.get("visual_balance", 0) for row in items
        ])
        if len(base) == 1:
            items[0].scores["temporal_peak"] = 0.5
            continue
        for index, item in enumerate(items):
            left = max(0, index - 2)
            right = min(len(items), index + 3)
            neighborhood = base[left:right]
            local_min = float(neighborhood.min())
            local_max = float(neighborhood.max())
            normalized = (float(base[index]) - local_min) / max(local_max - local_min, 1e-6)
            curvature = 0.0
            if 0 < index < len(items) - 1:
                curvature = max(0.0, float(base[index] - (base[index - 1] + base[index + 1]) / 2))
            item.scores["temporal_peak"] = float(np.clip(0.70 * normalized + 0.30 * min(1, curvature * 6), 0, 1))


def score_candidates(candidates: list[Candidate], mode: str) -> None:
    for item in candidates:
        scores = category_scores(item, mode)
        for name, value in scores.items():
            item.scores[f"category_{name.lower()}"] = round(value, 5)
        relevant = [scores[name] for name in item.labels if name in scores] or [scores["Other"]]
        item.scores["final"] = round(max(relevant), 5)


def mark_duplicates(candidates: list[Candidate], threshold: int = 7) -> list[Candidate]:
    accepted: list[Candidate] = []
    ordered = sorted(candidates, key=lambda row: row.final_score, reverse=True)
    for item in ordered:
        duplicate = None
        for kept in accepted:
            distance = hamming_distance(item.hash64, kept.hash64)
            same_shot = item.shot_id == kept.shot_id
            near_time = abs(item.timestamp - kept.timestamp) < 1.65
            if distance <= threshold and (same_shot or distance <= max(2, threshold - 4)) and (near_time or distance <= 2):
                duplicate = kept
                break
        if duplicate:
            item.duplicate_of = duplicate.id
        else:
            accepted.append(item)
    return accepted


def diversity_rank(candidates: list[Candidate], limit: int = 60) -> list[Candidate]:
    pool = [item for item in candidates if not item.rejected and not item.duplicate_of]
    selected: list[Candidate] = []
    category_counts = defaultdict(int)
    shot_counts = defaultdict(int)
    while pool and len(selected) < limit:
        best: Candidate | None = None
        best_value = -1.0
        for item in pool:
            main_category = max(
                item.labels,
                key=lambda label: item.scores.get(f"category_{label.lower()}", 0),
                default="Other",
            )
            category_bonus = 0.14 / (1 + category_counts[main_category])
            shot_penalty = 0.045 * shot_counts[item.shot_id]
            similarity_penalty = 0.0
            if selected:
                closest = min(hamming_distance(item.hash64, other.hash64) for other in selected)
                similarity_penalty = max(0.0, (12 - closest) / 12) * 0.16
            value = item.final_score + category_bonus - shot_penalty - similarity_penalty
            if value > best_value:
                best, best_value = item, value
        assert best is not None
        selected.append(best)
        pool.remove(best)
        main_category = max(
            best.labels,
            key=lambda label: best.scores.get(f"category_{label.lower()}", 0),
            default="Other",
        )
        category_counts[main_category] += 1
        shot_counts[best.shot_id] += 1
    for rank, item in enumerate(selected, 1):
        item.rank = rank
    return selected
