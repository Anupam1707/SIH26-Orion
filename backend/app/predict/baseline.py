"""Recency ranking and explicit heuristic per-ATM probabilities."""
import numpy as np

from app.predict.features import Features

RECENCY_DAYS = 14.


def spatial_scores(features: Features) -> np.ndarray:
    scores = np.exp(-features.last_age_days / RECENCY_DAYS)
    # No observed withdrawals means a uniform, explicitly uncertain fallback.
    return scores if scores.sum() > 0 else np.ones(len(features.atms))


def probabilities(scores: np.ndarray, expected_atms: float) -> np.ndarray:
    weights = scores / scores.sum() if scores.sum() else np.full(len(scores), 1 / len(scores))
    return -np.expm1(-weights * expected_atms)
