"""KDE bandwidth is selected on completed training cases only."""
import numpy as np
from sklearn.neighbors import KernelDensity

from app.predict.baseline import spatial_scores
from app.predict.features import Features

BANDWIDTHS_KM = (.25, .5, 1., 2., 4.)
DEFAULT_BANDWIDTH_KM = 1.


def density(features: Features, bandwidth: float) -> np.ndarray:
    if not len(features.history_xy):
        return np.zeros(len(features.atms))
    model = KernelDensity(bandwidth=bandwidth, kernel='gaussian').fit(features.history_xy)
    return np.exp(model.score_samples(features.atm_xy))


def choose_bandwidth(training_ids: list[str], features: dict[str, Features],
                     densities: dict[tuple[str, float], np.ndarray], labels: dict[str, np.ndarray]) -> float:
    """Prequential log score: each historical KDE uses only that case's past withdrawals."""
    if not training_ids:
        return DEFAULT_BANDWIDTH_KM
    losses = []
    for bandwidth in BANDWIDTHS_KM:
        per_case = []
        for cid in training_ids:
            if not len(features[cid].history):
                continue
            raw = densities[cid, bandwidth]
            probabilities = raw / raw.sum() if raw.sum() else spatial_scores(features[cid])
            actual = labels[cid].astype(bool)
            if actual.any():
                per_case.append(-float(np.log(np.maximum(probabilities[actual], 1e-15)).mean()))
        losses.append((float(np.mean(per_case)) if per_case else float('inf'), bandwidth))
    return min(losses)[1] if any(np.isfinite(loss) for loss, _ in losses) else DEFAULT_BANDWIDTH_KM
