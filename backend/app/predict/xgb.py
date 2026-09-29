"""Deterministic binary (case, ATM) classifiers with exact tree contributions."""
import numpy as np
import xgboost as xgb

from app.predict.features import FEATURE_NAMES


def fit(matrix: np.ndarray, labels: np.ndarray, seed: int) -> xgb.Booster | None:
    if not len(labels) or len(np.unique(labels)) < 2:
        return None
    train = xgb.DMatrix(matrix, label=labels, feature_names=FEATURE_NAMES, nthread=1)
    return xgb.train({'objective': 'binary:logistic', 'eval_metric': 'logloss',
                      'max_depth': 3, 'eta': .08, 'min_child_weight': 2,
                      'subsample': 1., 'colsample_bytree': 1., 'lambda': 2.,
                      'tree_method': 'hist', 'nthread': 1, 'seed': seed}, train, num_boost_round=80)


def predict(model: xgb.Booster, matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    data = xgb.DMatrix(matrix, feature_names=FEATURE_NAMES, nthread=1)
    return model.predict(data), model.predict(data, pred_contribs=True)
