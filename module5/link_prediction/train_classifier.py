"""
train_classifier.py — Module 5 Tier 3: Level 2 Supervised ML Classifier
=========================================================================
Trains and evaluates three classifiers on the edge feature vectors produced
by feature_pipeline.py.

Models
------
  * Logistic Regression      (linear sanity-check)
  * Random Forest (n=300)    (strong tabular baseline)
  * Gradient Boosting        (sklearn HistGradientBoostingClassifier)

Evaluation
----------
  * AUC-ROC, Average Precision (PR-AUC), Precision@K (K=10, 50)
  * Feature importance table (Random Forest)
  * Best model saved to best_model.pkl

Outputs (module5/data/link_prediction/)
----------------------------------------
    clf_results_{graph}.csv       — per-model val + test metrics
    feature_importance_{graph}.csv
    best_model_{graph}.pkl

Run
---
    python module5/link_prediction/train_classifier.py
    python module5/link_prediction/train_classifier.py --graph financial
"""

from __future__ import annotations

import argparse
import pickle
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    GradientBoostingClassifier,
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

ROOT   = Path(__file__).resolve().parent.parent.parent
LP_DIR = ROOT / "module5" / "data" / "link_prediction"

GRAPHS = {
    "financial":     ("source_account_id", "target_account_id"),
    "communication": ("source_phone_id",   "target_phone_id"),
}

LABEL_COL = "label"


# ── classifiers ────────────────────────────────────────────────────────────────

def _make_classifiers() -> dict:
    return {
        "LogisticRegression": Pipeline([
            ("scaler", StandardScaler()),
            ("clf",    LogisticRegression(max_iter=1000, class_weight="balanced",
                                          C=1.0, random_state=42)),
        ]),
        "RandomForest": RandomForestClassifier(
            n_estimators=300, max_depth=None, min_samples_leaf=2,
            class_weight="balanced", n_jobs=-1, random_state=42,
        ),
        "HistGradientBoosting": HistGradientBoostingClassifier(
            max_iter=300, max_depth=6, learning_rate=0.05,
            min_samples_leaf=20, l2_regularization=0.1,
            class_weight="balanced", random_state=42,
        ),
    }


# ── helpers ────────────────────────────────────────────────────────────────────

def _load_features(split: str, graph_name: str,
                   src_col: str, dst_col: str) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    path = LP_DIR / f"features_{split}_{graph_name}.parquet"
    df   = pd.read_parquet(path)
    drop = [src_col, dst_col, LABEL_COL]
    drop = [c for c in drop if c in df.columns]
    X    = df.drop(columns=drop).values.astype(np.float64)
    y    = df[LABEL_COL].values.astype(int)
    return X, y, df


def _precision_at_k(y_true: np.ndarray, y_score: np.ndarray, k: int) -> float:
    top_idx = np.argsort(-y_score)[:k]
    return float(y_true[top_idx].mean()) if len(top_idx) >= k else float("nan")


def _evaluate_model(clf, X_val, y_val, X_test, y_test) -> dict:
    results = {}
    for split_name, X, y in [("val", X_val, y_val), ("test", X_test, y_test)]:
        y_score = clf.predict_proba(X)[:, 1]
        results[split_name] = {
            "auc":  roc_auc_score(y, y_score),
            "ap":   average_precision_score(y, y_score),
            "p@10": _precision_at_k(y, y_score, 10),
            "p@50": _precision_at_k(y, y_score, 50),
        }
    return results


# ── main ───────────────────────────────────────────────────────────────────────

def run_graph(graph_name: str) -> None:
    src_col, dst_col = GRAPHS[graph_name]
    print(f"\n── {graph_name} graph ──")

    # check feature files exist
    for split in ("train", "val", "test"):
        p = LP_DIR / f"features_{split}_{graph_name}.parquet"
        if not p.exists():
            print(f"  Missing {p.name}. Run feature_pipeline.py first.")
            return

    X_train, y_train, _     = _load_features("train", graph_name, src_col, dst_col)
    X_val,   y_val,   val_df = _load_features("val",   graph_name, src_col, dst_col)
    X_test,  y_test,  test_df = _load_features("test",  graph_name, src_col, dst_col)

    feature_names = test_df.drop(
        columns=[c for c in [src_col, dst_col, LABEL_COL] if c in test_df.columns]
    ).columns.tolist()

    print(f"  Train: {X_train.shape}  Val: {X_val.shape}  Test: {X_test.shape}")
    print(f"  Positive rate — train: {y_train.mean():.3f}  val: {y_val.mean():.3f}  test: {y_test.mean():.3f}")

    classifiers = _make_classifiers()
    records     = []
    best_val_auc = -1.0
    best_name    = None
    best_clf     = None

    print(f"\n  {'Model':<30} {'Val AUC':>9} {'Val AP':>9} {'Test AUC':>10} {'Test AP':>9}")
    print("  " + "-" * 72)

    for name, clf in classifiers.items():
        print(f"  Training {name} …", end="\r")
        clf.fit(X_train, y_train)
        res = _evaluate_model(clf, X_val, y_val, X_test, y_test)

        v, t = res["val"], res["test"]
        print(f"  {name:<30} {v['auc']:>9.4f} {v['ap']:>9.4f} {t['auc']:>10.4f} {t['ap']:>9.4f}")

        for split, m in res.items():
            records.append({
                "graph": graph_name, "model": name, "split": split,
                **m
            })

        if v["auc"] > best_val_auc:
            best_val_auc = v["auc"]
            best_name    = name
            best_clf     = clf

    print(f"\n  ✓ Best model: {best_name}  (val AUC = {best_val_auc:.4f})")

    # save results
    results_df = pd.DataFrame(records)
    results_df.to_csv(LP_DIR / f"clf_results_{graph_name}.csv", index=False)

    # feature importance (RF only)
    if hasattr(best_clf, "feature_importances_"):
        fi = pd.DataFrame({
            "feature": feature_names,
            "importance": best_clf.feature_importances_,
        }).sort_values("importance", ascending=False)
    elif hasattr(best_clf, "named_steps"):
        inner = best_clf.named_steps.get("clf")
        if hasattr(inner, "coef_"):
            fi = pd.DataFrame({
                "feature": feature_names,
                "importance": np.abs(inner.coef_[0]),
            }).sort_values("importance", ascending=False)
        else:
            fi = pd.DataFrame({"feature": feature_names, "importance": [float("nan")] * len(feature_names)})
    else:
        fi = pd.DataFrame({"feature": feature_names, "importance": [float("nan")] * len(feature_names)})

    fi_path = LP_DIR / f"feature_importance_{graph_name}.csv"
    fi.to_csv(fi_path, index=False)
    print(f"\n  Top-10 features by importance:")
    print(fi.head(10).to_string(index=False))

    # save best model
    model_path = LP_DIR / f"best_model_{graph_name}.pkl"
    with open(model_path, "wb") as f:
        pickle.dump({"model": best_clf, "name": best_name,
                     "feature_names": feature_names,
                     "graph": graph_name,
                     "src_col": src_col, "dst_col": dst_col}, f, protocol=4)
    print(f"\n  Best model saved → {model_path.name}")


def main(graphs: list[str] | None = None) -> None:
    if graphs is None:
        graphs = list(GRAPHS.keys())

    print("=" * 60)
    print("Module 5 Tier 3 — Level 2 Supervised Classifiers")
    print("=" * 60)

    for g in graphs:
        run_graph(g)

    print("\nDone. Run gnn_embedder.py next.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", choices=list(GRAPHS.keys()))
    args = parser.parse_args()
    main(graphs=[args.graph] if args.graph else None)
