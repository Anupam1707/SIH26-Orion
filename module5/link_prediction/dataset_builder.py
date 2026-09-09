"""
dataset_builder.py — Module 5 Tier 3: Link Prediction Dataset Builder
======================================================================
Builds train / val / test edge splits for both the financial graph
(Account → Account via transactions) and the communication graph
(Phone → Phone via CDR communications).

Strategy
--------
* Edges are sorted chronologically.
* Split: 70% train | 15% val | 15% test  (by edge timestamp, not randomly)
* For every positive held-out edge, 5 × random negative pairs are sampled
  (both nodes present in training graph; edge absent from training graph).
* An additional pool of hard negatives is created from 2-hop non-edge pairs
  that share at least 1 common neighbor in the training graph.

Outputs (written to module5/data/link_prediction/)
---------------------------------------------------
    train_pos_{graph}.csv, train_neg_{graph}.csv
    val_pos_{graph}.csv,   val_neg_{graph}.csv
    test_pos_{graph}.csv,  test_neg_{graph}.csv
    graph_train_{graph}.gpickle
    split_stats.txt

Run
---
    python module5/link_prediction/dataset_builder.py
"""

from __future__ import annotations

import os
import random
import pickle
import textwrap
from pathlib import Path

import networkx as nx
import pandas as pd
import numpy as np

# ── paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent          # SIH26/
DATA_REL = ROOT / "data" / "dataset" / "RELATIONSHIPS"
OUT_DIR   = ROOT / "module5" / "data" / "link_prediction"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_SEED   = 42
NEG_RATIO     = 5        # negatives per positive edge
HARD_NEG_FRAC = 0.3      # fraction of negatives drawn from 2-hop pool
TRAIN_FRAC    = 0.70
VAL_FRAC      = 0.15     # remainder → test


# ── helpers ───────────────────────────────────────────────────────────────────

def _temporal_split(df: pd.DataFrame,
                    timestamp_col: str,
                    src_col: str,
                    dst_col: str,
                    extra_cols: list[str] | None = None) -> tuple[
                        pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Sort by timestamp, then cut 70 / 15 / 15."""
    df = df.copy()
    df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors="coerce")
    df = df.dropna(subset=[timestamp_col]).sort_values(timestamp_col)
    n = len(df)
    i_train = int(n * TRAIN_FRAC)
    i_val   = int(n * (TRAIN_FRAC + VAL_FRAC))

    keep = [src_col, dst_col, timestamp_col] + (extra_cols or [])
    keep = [c for c in keep if c in df.columns]
    train = df.iloc[:i_train][keep].copy()
    val   = df.iloc[i_train:i_val][keep].copy()
    test  = df.iloc[i_val:][keep].copy()
    return train, val, test


def _build_nx_graph(df: pd.DataFrame,
                    src_col: str, dst_col: str,
                    directed: bool = True) -> nx.Graph:
    G = nx.DiGraph() if directed else nx.Graph()
    for _, row in df.iterrows():
        G.add_edge(row[src_col], row[dst_col])
    return G


def _sample_negatives(
    pos_df: pd.DataFrame,
    src_col: str,
    dst_col: str,
    train_G: nx.Graph,
    all_nodes: list,
    hard_negatives: set[tuple],
    n_per_pos: int = NEG_RATIO,
    hard_frac: float = HARD_NEG_FRAC,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    """
    For each positive edge, sample n_per_pos negatives:
      - hard_frac from the 2-hop non-edge pool (if available)
      - remainder randomly
    Both endpoints must be in the training graph.
    """
    rng = random.Random(seed)
    train_nodes = list(train_G.nodes())
    existing = set(zip(pos_df[src_col], pos_df[dst_col]))
    train_edges = set(train_G.edges())
    hard_pool = list(hard_negatives - existing - train_edges)

    records = []
    n_hard  = max(0, int(n_per_pos * hard_frac))
    n_rand  = n_per_pos - n_hard

    for _ in range(len(pos_df)):
        # hard negatives
        chosen_hard = rng.sample(hard_pool, min(n_hard, len(hard_pool)))
        for (u, v) in chosen_hard:
            records.append({src_col: u, dst_col: v, "label": 0, "neg_type": "hard"})

        # random negatives
        attempts = 0
        got = 0
        while got < n_rand and attempts < 5000:
            u = rng.choice(train_nodes)
            v = rng.choice(train_nodes)
            attempts += 1
            if (u == v
                    or (u, v) in train_edges
                    or (u, v) in existing
                    or not train_G.has_node(u)
                    or not train_G.has_node(v)):
                continue
            records.append({src_col: u, dst_col: v, "label": 0, "neg_type": "random"})
            train_edges.add((u, v))   # avoid duplicating within this run
            got += 1

    return pd.DataFrame(records)


def _hard_neg_pool(train_G: nx.Graph) -> set[tuple]:
    """2-hop pairs that share ≥ 1 neighbor but have no direct edge (undirected)."""
    U = train_G.to_undirected()
    pool: set[tuple] = set()
    for node in U.nodes():
        neighbors = list(U.neighbors(node))
        for i in range(len(neighbors)):
            for j in range(i + 1, len(neighbors)):
                u, v = neighbors[i], neighbors[j]
                if not U.has_edge(u, v):
                    pool.add((u, v))
    return pool


def _save_split(pos: pd.DataFrame, neg: pd.DataFrame,
                src_col: str, dst_col: str,
                prefix: str, graph_name: str) -> None:
    pos_out = pos.copy()
    pos_out["label"] = 1
    pos_out.to_csv(OUT_DIR / f"{prefix}_pos_{graph_name}.csv", index=False)

    neg_out = neg[[src_col, dst_col, "label", "neg_type"]].copy()
    neg_out.to_csv(OUT_DIR / f"{prefix}_neg_{graph_name}.csv", index=False)

    print(f"  [{graph_name}] {prefix}: {len(pos_out)} pos, {len(neg_out)} neg")


# ── financial graph ────────────────────────────────────────────────────────────

def build_financial_graph() -> None:
    print("\n── Financial graph (Account → Account) ──")
    tx = pd.read_csv(DATA_REL / "transactions.csv")
    train_df, val_df, test_df = _temporal_split(
        tx, "timestamp", "source_account_id", "target_account_id",
        extra_cols=["amount", "transaction_type", "channel"]
    )
    src, dst = "source_account_id", "target_account_id"

    train_G = _build_nx_graph(train_df, src, dst)
    print(f"  Training graph: {train_G.number_of_nodes()} nodes, "
          f"{train_G.number_of_edges()} edges")

    # save training graph
    graph_path = OUT_DIR / "graph_train_financial.pkl"
    with open(graph_path, "wb") as f:
        pickle.dump(train_G, f, protocol=4)

    # build hard neg pool
    print("  Building hard negative pool …")
    hard_pool = _hard_neg_pool(train_G)
    print(f"  Hard negative pool: {len(hard_pool)} pairs")

    all_nodes = list(train_G.nodes())

    # val
    val_pos = val_df[[src, dst, "timestamp"]].copy()
    val_neg = _sample_negatives(val_pos, src, dst, train_G, all_nodes, hard_pool, seed=1)
    _save_split(val_pos, val_neg, src, dst, "val", "financial")

    # test
    test_pos = test_df[[src, dst, "timestamp"]].copy()
    test_neg = _sample_negatives(test_pos, src, dst, train_G, all_nodes, hard_pool, seed=2)
    _save_split(test_pos, test_neg, src, dst, "test", "financial")

    # train self-supervised (hold-out within train set for GNN pre-train)
    n_tr_hold = int(len(train_df) * 0.10)
    train_pos = train_df.iloc[:-n_tr_hold][[src, dst, "timestamp"]].copy()
    train_held = train_df.iloc[-n_tr_hold:][[src, dst, "timestamp"]].copy()
    train_neg = _sample_negatives(train_held, src, dst, train_G, all_nodes, hard_pool, seed=3)
    _save_split(train_held, train_neg, src, dst, "train", "financial")

    return train_G


# ── communication graph ────────────────────────────────────────────────────────

def build_communication_graph() -> None:
    print("\n── Communication graph (Phone → Phone) ──")
    comm = pd.read_csv(DATA_REL / "communications.csv")
    train_df, val_df, test_df = _temporal_split(
        comm, "timestamp", "source_phone_id", "target_phone_id",
        extra_cols=["communication_type", "duration_seconds"]
    )
    src, dst = "source_phone_id", "target_phone_id"

    train_G = _build_nx_graph(train_df, src, dst)
    print(f"  Training graph: {train_G.number_of_nodes()} nodes, "
          f"{train_G.number_of_edges()} edges")

    graph_path = OUT_DIR / "graph_train_communication.pkl"
    with open(graph_path, "wb") as f:
        pickle.dump(train_G, f, protocol=4)

    print("  Building hard negative pool …")
    hard_pool = _hard_neg_pool(train_G)
    print(f"  Hard negative pool: {len(hard_pool)} pairs")

    all_nodes = list(train_G.nodes())

    val_pos = val_df[[src, dst, "timestamp"]].copy()
    val_neg = _sample_negatives(val_pos, src, dst, train_G, all_nodes, hard_pool, seed=4)
    _save_split(val_pos, val_neg, src, dst, "val", "communication")

    test_pos = test_df[[src, dst, "timestamp"]].copy()
    test_neg = _sample_negatives(test_pos, src, dst, train_G, all_nodes, hard_pool, seed=5)
    _save_split(test_pos, test_neg, src, dst, "test", "communication")

    n_tr_hold = int(len(train_df) * 0.10)
    train_held = train_df.iloc[-n_tr_hold:][[src, dst, "timestamp"]].copy()
    train_neg = _sample_negatives(train_held, src, dst, train_G, all_nodes, hard_pool, seed=6)
    _save_split(train_held, train_neg, src, dst, "train", "communication")

    return train_G


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    print("=" * 60)
    print("Module 5 Tier 3 — Dataset Builder")
    print(f"Output directory: {OUT_DIR}")
    print("=" * 60)

    fin_G  = build_financial_graph()
    comm_G = build_communication_graph()

    # ── summary ──
    stats = textwrap.dedent(f"""
    === Split Statistics ===

    Financial graph (Account→Account via transactions)
      Training graph : {fin_G.number_of_nodes()} nodes, {fin_G.number_of_edges()} edges
      Neg ratio      : {NEG_RATIO}:1   Hard neg frac: {HARD_NEG_FRAC}

    Communication graph (Phone→Phone via CDR)
      Training graph : {comm_G.number_of_nodes()} nodes, {comm_G.number_of_edges()} edges
      Neg ratio      : {NEG_RATIO}:1   Hard neg frac: {HARD_NEG_FRAC}

    Temporal split   : {int(TRAIN_FRAC*100)}% train | {int(VAL_FRAC*100)}% val | {int((1-TRAIN_FRAC-VAL_FRAC)*100)}% test
    Random seed      : {RANDOM_SEED}

    Output files written to: {OUT_DIR}
    """).strip()
    print("\n" + stats)
    (OUT_DIR / "split_stats.txt").write_text(stats)
    print("\nDone. Run heuristics.py next.")


if __name__ == "__main__":
    main()
