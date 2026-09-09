"""
heuristics.py — Module 5 Tier 3: Level 1 Link Prediction Baselines
====================================================================
Computes classical structural link-prediction heuristics on the training
graph and evaluates them against the val and test splits.

Heuristics
----------
  * Common Neighbors (CN)
  * Jaccard Coefficient
  * Adamic-Adar (AA)
  * Resource Allocation (RA)
  * Preferential Attachment (PA)

Metrics
-------
  * AUC-ROC
  * Average Precision (PR-AUC)
  * Precision@K  (K = 10, 50)

Outputs (module5/data/link_prediction/)
----------------------------------------
    heuristics_val_{graph}.csv
    heuristics_test_{graph}.csv
    heuristics_summary.txt

Run
---
    python module5/link_prediction/heuristics.py
    python module5/link_prediction/heuristics.py --graph financial
    python module5/link_prediction/heuristics.py --graph communication
"""

from __future__ import annotations

import argparse
import math
import pickle
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

# ── paths ──────────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).resolve().parent.parent.parent
LP_DIR  = ROOT / "module5" / "data" / "link_prediction"

GRAPHS = {
    "financial":     ("source_account_id", "target_account_id"),
    "communication": ("source_phone_id",   "target_phone_id"),
}


# ── heuristic functions ────────────────────────────────────────────────────────

def _common_neighbors(U: nx.Graph, u: str, v: str) -> float:
    return float(len(list(nx.common_neighbors(U, u, v))))


def _jaccard(U: nx.Graph, u: str, v: str) -> float:
    nu = set(U.neighbors(u))
    nv = set(U.neighbors(v))
    denom = len(nu | nv)
    return len(nu & nv) / denom if denom else 0.0


def _adamic_adar(U: nx.Graph, u: str, v: str) -> float:
    score = 0.0
    for w in nx.common_neighbors(U, u, v):
        deg = U.degree(w)
        if deg > 1:
            score += 1.0 / math.log(deg)
    return score


def _resource_allocation(U: nx.Graph, u: str, v: str) -> float:
    score = 0.0
    for w in nx.common_neighbors(U, u, v):
        deg = U.degree(w)
        if deg > 0:
            score += 1.0 / deg
    return score


def _preferential_attachment(U: nx.Graph, u: str, v: str) -> float:
    return float(U.degree(u) * U.degree(v))


HEURISTIC_FNS = {
    "common_neighbors":       _common_neighbors,
    "jaccard":                _jaccard,
    "adamic_adar":            _adamic_adar,
    "resource_allocation":    _resource_allocation,
    "preferential_attachment": _preferential_attachment,
}


# ── scoring ────────────────────────────────────────────────────────────────────

def _score_pairs(
    U: nx.Graph,
    pos_df: pd.DataFrame,
    neg_df: pd.DataFrame,
    src_col: str,
    dst_col: str,
) -> pd.DataFrame:
    """Score all (pos ∪ neg) pairs with every heuristic. Returns scored DataFrame."""
    pos = pos_df[[src_col, dst_col]].copy()
    pos["label"] = 1
    neg = neg_df[[src_col, dst_col]].copy()
    neg["label"] = 0

    df = pd.concat([pos, neg], ignore_index=True)

    for hname, hfn in HEURISTIC_FNS.items():
        scores = []
        for _, row in df.iterrows():
            u, v = str(row[src_col]), str(row[dst_col])
            if U.has_node(u) and U.has_node(v):
                scores.append(hfn(U, u, v))
            else:
                scores.append(0.0)
        df[hname] = scores

    return df


def _evaluate(df: pd.DataFrame, split_name: str, graph_name: str) -> dict[str, dict]:
    """Print AUC-ROC, AP, Precision@K for each heuristic."""
    y_true = df["label"].values
    results = {}
    print(f"\n  [{graph_name}] {split_name} set  ({y_true.sum():.0f} pos / {(1-y_true).sum():.0f} neg)")
    print(f"  {'Heuristic':<28} {'AUC-ROC':>8} {'AP':>8} {'P@10':>8} {'P@50':>8}")
    print("  " + "-" * 58)

    for hname in HEURISTIC_FNS:
        y_score = df[hname].values
        try:
            auc = roc_auc_score(y_true, y_score)
            ap  = average_precision_score(y_true, y_score)
        except ValueError:
            auc, ap = float("nan"), float("nan")

        # Precision@K
        top_idx = np.argsort(-y_score)
        pk10 = y_true[top_idx[:10]].mean()  if len(top_idx) >= 10  else float("nan")
        pk50 = y_true[top_idx[:50]].mean()  if len(top_idx) >= 50  else float("nan")

        results[hname] = {"auc": auc, "ap": ap, "p@10": pk10, "p@50": pk50}
        print(f"  {hname:<28} {auc:>8.4f} {ap:>8.4f} {pk10:>8.4f} {pk50:>8.4f}")

    return results


# ── main ───────────────────────────────────────────────────────────────────────

def run_graph(graph_name: str) -> dict:
    src_col, dst_col = GRAPHS[graph_name]

    # load training graph
    graph_path = LP_DIR / f"graph_train_{graph_name}.pkl"
    if not graph_path.exists():
        raise FileNotFoundError(
            f"Training graph not found: {graph_path}\n"
            "Run dataset_builder.py first."
        )
    with open(graph_path, "rb") as f:
        train_G: nx.DiGraph = pickle.load(f)

    # undirected projection for heuristic scoring
    U = train_G.to_undirected()
    print(f"\nLoaded {graph_name} training graph: "
          f"{U.number_of_nodes()} nodes, {U.number_of_edges()} edges")

    all_results: dict = {}

    for split in ("val", "test"):
        pos_path = LP_DIR / f"{split}_pos_{graph_name}.csv"
        neg_path = LP_DIR / f"{split}_neg_{graph_name}.csv"
        if not pos_path.exists():
            print(f"  Skipping {split} (files not found — run dataset_builder.py first)")
            continue

        pos_df = pd.read_csv(pos_path)
        neg_df = pd.read_csv(neg_path)

        scored = _score_pairs(U, pos_df, neg_df, src_col, dst_col)
        out_path = LP_DIR / f"heuristics_{split}_{graph_name}.csv"
        scored.to_csv(out_path, index=False)

        all_results[split] = _evaluate(scored, split, graph_name)

    return all_results


def main(graphs: list[str] | None = None) -> None:
    if graphs is None:
        graphs = list(GRAPHS.keys())

    print("=" * 60)
    print("Module 5 Tier 3 — Level 1 Heuristic Baselines")
    print("=" * 60)

    summary_lines = []
    for graph_name in graphs:
        res = run_graph(graph_name)

        for split, scores in res.items():
            for hname, metrics in scores.items():
                summary_lines.append(
                    f"{graph_name},{split},{hname},"
                    f"{metrics['auc']:.4f},{metrics['ap']:.4f},"
                    f"{metrics['p@10']:.4f},{metrics['p@50']:.4f}"
                )

    # save summary
    header = "graph,split,heuristic,auc_roc,avg_precision,precision_at_10,precision_at_50"
    summary_text = header + "\n" + "\n".join(summary_lines)
    summary_path = LP_DIR / "heuristics_summary.csv"
    summary_path.write_text(summary_text)
    print(f"\nSummary saved → {summary_path}")
    print("\nDone. Run feature_pipeline.py next.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Link prediction heuristic baselines")
    parser.add_argument(
        "--graph", choices=list(GRAPHS.keys()),
        help="Which graph to run. Default: both."
    )
    args = parser.parse_args()
    main(graphs=[args.graph] if args.graph else None)
