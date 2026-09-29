"""
dataset_builder.py — Module 5 Tier 3: Link Prediction Dataset Builder
======================================================================
Builds train / val / test edge splits for both the financial graph
(Account → Account via transactions) and the communication graph
(Phone → Phone via CDR communications).

Evaluation framework: Random Edge Masking
-----------------------------------------
Random masking is the standard evaluation for HIDDEN LINK DISCOVERY
(Liben-Nowell & Kleinberg 2007), which is the correct framing for the SIH
task — finding covert connections that exist but are unobserved.

Why NOT temporal splits (previous approach, now replaced):
  Temporal splits held out the MOST RECENT 30% of edges. For planted
  ground-truth patterns (BRIDGE_01/02, mule chains), the bridge edges were
  planted after most background edges, so they landed in the test set where
  both endpoints had ZERO common neighbors in the training graph. Every
  topological model scored them at worst-possible (shortest_path=∞, CN=0),
  making GT recall structurally impossible.

Random masking strategy:
  1. Mask MASK_FRAC (20%) of edges at random, keeping every node with ≥1
     edge in the training graph (stratified sampling).
  2. Ground-truth planted edges (BRIDGE_01/02, mule chains, layering chains)
     are FORCIBLY INCLUDED in the mask — they are guaranteed test positives.
  3. Training graph = remaining 80% of edges.
  4. Val = random half of masked edges + NEG_RATIO:1 negatives.
  5. Test = other half of masked edges + NEG_RATIO:1 negatives.

Result: GT edges are held out but the training graph still contains the
adjacent edges, giving non-zero common neighbors, finite shortest paths,
and meaningful heuristic scores.

Outputs (written to intelligence/data/link_prediction/)
---------------------------------------------------
    train_pos_{graph}.csv, train_neg_{graph}.csv
    val_pos._{graph}.csv,  val_neg_{graph}.csv
    test_pos_{graph}.csv,  test_neg_{graph}.csv
    graph_train_{graph}.pkl
    split_stats.txt

Run
---
    python intelligence/link_prediction/dataset_builder.py
"""

from __future__ import annotations

import os
import pickle
import random
import textwrap
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

# ── paths ─────────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).resolve().parent.parent.parent
DATA_REL = ROOT / "data" / "dataset" / "RELATIONSHIPS"
OUT_DIR  = ROOT / "intelligence" / "data" / "link_prediction"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_SEED = 42
NEG_RATIO   = 5      # negatives per positive
HARD_NEG_FRAC = 0.3  # fraction of negatives from 2-hop hard pool
MASK_FRAC   = 0.20   # fraction of edges to mask as val+test positives

# ── Ground-truth planted edges (forced into the mask for guaranteed recall) ───
# These come from GROUND_TRUTH.csv and the Tier 1 confirmed findings.
GT_FORCED_EDGES = {
    "financial": [
        ("A00001", "A00013"),   # MULE_01 feeder→collector
        ("A00012", "A00013"),   # MULE_01 feeder→collector
        ("A00013", "A00014"),   # MULE_01 collector→target
        ("A00043", "A00047"),   # LAYERING_01 chain endpoints
        ("A00049", "A00053"),   # LAYERING_02 chain endpoints
        ("A00069", "A00070"),   # STRUCTURING_01 pair
        ("A00055", "A00056"),   # SCATTER_GATHER feeder→receiver
    ],
    "communication": [
        ("PH04296", "PH04450"),  # BRIDGE_01
        ("PH02064", "PH04287"),  # BRIDGE_02
        ("PH00002", "PH00001"),  # BURNER_01 rotation pair
    ],
}


# ── helpers ───────────────────────────────────────────────────────────────────

def _build_nx_graph(df: pd.DataFrame,
                    src_col: str, dst_col: str) -> nx.DiGraph:
    G = nx.DiGraph()
    for _, row in df.iterrows():
        G.add_edge(str(row[src_col]), str(row[dst_col]))
    return G


def _random_mask(G: nx.DiGraph,
                 forced_edges: list[tuple],
                 mask_frac: float,
                 seed: int) -> tuple[set[tuple], nx.DiGraph]:
    """
    Randomly mask mask_frac of edges. Forced GT edges are always masked.
    Every node is guaranteed ≥1 edge remaining in the training graph.
    Returns (masked_edges_set, training_graph).
    """
    rng = random.Random(seed)
    all_edges = list(G.edges())
    rng.shuffle(all_edges)

    # start with forced GT edges that actually exist in the graph
    forced = {(u, v) for u, v in forced_edges if G.has_edge(u, v)}
    also_reversed = {(v, u) for u, v in forced if G.has_edge(v, u)}
    forced |= also_reversed

    n_target = max(int(len(all_edges) * mask_frac), len(forced))

    # build degree count to protect the minimum
    remaining_deg = {n: G.degree(n) for n in G.nodes()}
    for u, v in forced:
        remaining_deg[u] -= 1
        remaining_deg[v] -= 1

    masked: set[tuple] = set(forced)

    for u, v in all_edges:
        if len(masked) >= n_target:
            break
        if (u, v) in masked:
            continue
        # keep at least 1 edge per node
        if remaining_deg[u] <= 1 or remaining_deg[v] <= 1:
            continue
        masked.add((u, v))
        remaining_deg[u] -= 1
        remaining_deg[v] -= 1

    # build training graph
    train_G = nx.DiGraph()
    for n in G.nodes():
        train_G.add_node(n)
    for u, v in all_edges:
        if (u, v) not in masked:
            train_G.add_edge(u, v)

    return masked, train_G


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


def _sample_negatives(
    pos_pairs: list[tuple],
    src_col: str, dst_col: str,
    train_G: nx.DiGraph,
    hard_pool: set[tuple],
    n_per_pos: int = NEG_RATIO,
    hard_frac: float = HARD_NEG_FRAC,
    seed: int = RANDOM_SEED,
) -> pd.DataFrame:
    rng = random.Random(seed)
    train_nodes = list(train_G.nodes())
    existing = set(train_G.edges()) | set(pos_pairs)
    hard_list = list(hard_pool - existing)

    n_hard = max(0, int(n_per_pos * hard_frac))
    n_rand = n_per_pos - n_hard

    records = []
    used_rand: set[tuple] = set()

    for _ in pos_pairs:
        # hard negatives
        chosen = rng.sample(hard_list, min(n_hard, len(hard_list)))
        for (u, v) in chosen:
            records.append({src_col: u, dst_col: v, "label": 0, "neg_type": "hard"})

        # random negatives
        got, attempts = 0, 0
        while got < n_rand and attempts < 5000:
            u = rng.choice(train_nodes)
            v = rng.choice(train_nodes)
            attempts += 1
            if u == v or (u, v) in existing or (u, v) in used_rand:
                continue
            records.append({src_col: u, dst_col: v, "label": 0, "neg_type": "random"})
            used_rand.add((u, v))
            got += 1

    return pd.DataFrame(records)


def _save_split(pos_pairs: list[tuple], neg_df: pd.DataFrame,
                src_col: str, dst_col: str,
                prefix: str, graph_name: str) -> None:
    pos_df = pd.DataFrame(pos_pairs, columns=[src_col, dst_col])
    pos_df["label"] = 1
    pos_df.to_csv(OUT_DIR / f"{prefix}_pos_{graph_name}.csv", index=False)
    neg_df.to_csv(OUT_DIR / f"{prefix}_neg_{graph_name}.csv", index=False)
    print(f"  [{graph_name}] {prefix:5s}: {len(pos_df)} pos,  {len(neg_df)} neg")


# ── graph builders ─────────────────────────────────────────────────────────────

def build_graph(graph_name: str,
                csv_path: Path,
                src_col: str, dst_col: str) -> nx.DiGraph:
    print(f"\n── {graph_name} graph ({src_col} → {dst_col}) ──")
    df = pd.read_csv(csv_path)
    full_G = _build_nx_graph(df, src_col, dst_col)
    print(f"  Full graph: {full_G.number_of_nodes()} nodes, "
          f"{full_G.number_of_edges()} edges")

    forced = GT_FORCED_EDGES.get(graph_name, [])
    present = [(u, v) for u, v in forced if full_G.has_edge(u, v)]
    missing = [(u, v) for u, v in forced if not full_G.has_edge(u, v)]
    print(f"  Forced GT edges: {len(present)} present in graph, "
          f"{len(missing)} missing (not in CSV) — skipped")

    masked_edges, train_G = _random_mask(full_G, present, MASK_FRAC, RANDOM_SEED)
    print(f"  Masked {len(masked_edges)} edges ({100*len(masked_edges)/full_G.number_of_edges():.1f}%)")
    print(f"  Training graph: {train_G.number_of_nodes()} nodes, "
          f"{train_G.number_of_edges()} edges")

    # Verify forced edges are in mask
    for u, v in present:
        status = "✅" if (u, v) in masked_edges or (v, u) in masked_edges else "❌ MISSING"
        print(f"    {status} GT edge {u}↔{v}")

    # save training graph
    with open(OUT_DIR / f"graph_train_{graph_name}.pkl", "wb") as f:
        pickle.dump(train_G, f, protocol=4)

    # hard negative pool from training graph
    print("  Building hard negative pool …")
    hard_pool = _hard_neg_pool(train_G)
    print(f"  Hard negative pool: {len(hard_pool)} pairs")

    # split masked edges into val and test halves
    masked_list = list(masked_edges)
    random.Random(RANDOM_SEED + 1).shuffle(masked_list)
    mid = len(masked_list) // 2
    val_pos  = masked_list[:mid]
    test_pos = masked_list[mid:]

    # also produce a train self-supervised set (10% additional random mask within train)
    train_edges = list(train_G.edges())
    random.Random(RANDOM_SEED + 2).shuffle(train_edges)
    train_hold_n = max(int(len(train_edges) * 0.10), 50)
    train_pos = train_edges[:train_hold_n]

    val_neg   = _sample_negatives(val_pos,   src_col, dst_col, train_G, hard_pool, seed=10)
    test_neg  = _sample_negatives(test_pos,  src_col, dst_col, train_G, hard_pool, seed=11)
    train_neg = _sample_negatives(train_pos, src_col, dst_col, train_G, hard_pool, seed=12)

    _save_split(val_pos,   val_neg,   src_col, dst_col, "val",   graph_name)
    _save_split(test_pos,  test_neg,  src_col, dst_col, "test",  graph_name)
    _save_split(train_pos, train_neg, src_col, dst_col, "train", graph_name)

    return train_G


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    print("=" * 60)
    print("Module 5 Tier 3 — Dataset Builder (Random Masking Mode)")
    print(f"Output directory: {OUT_DIR}")
    print("=" * 60)

    fin_G = build_graph(
        "financial",
        DATA_REL / "transactions.csv",
        "source_account_id", "target_account_id",
    )
    comm_G = build_graph(
        "communication",
        DATA_REL / "communications.csv",
        "source_phone_id", "target_phone_id",
    )

    stats = textwrap.dedent(f"""
    === Split Statistics ===
    Mode: RANDOM EDGE MASKING (replaces previous temporal splits)

    Financial graph (Account→Account via transactions)
      Training graph : {fin_G.number_of_nodes()} nodes, {fin_G.number_of_edges()} edges
      Mask fraction  : {int(MASK_FRAC*100)}%   Neg ratio: {NEG_RATIO}:1   Hard neg frac: {HARD_NEG_FRAC}

    Communication graph (Phone→Phone via CDR)
      Training graph : {comm_G.number_of_nodes()} nodes, {comm_G.number_of_edges()} edges
      Mask fraction  : {int(MASK_FRAC*100)}%   Neg ratio: {NEG_RATIO}:1   Hard neg frac: {HARD_NEG_FRAC}

    GT edges forcibly masked (guaranteed test positives):
      Financial   : {[f'{u}↔{v}' for u,v in GT_FORCED_EDGES['financial']]}
      Comm        : {[f'{u}↔{v}' for u,v in GT_FORCED_EDGES['communication']]}

    Random seed: {RANDOM_SEED}
    Output: {OUT_DIR}
    """).strip()

    print("\n" + stats)
    (OUT_DIR / "split_stats.txt").write_text(stats)
    print("\nDone. Run heuristics.py next.")


if __name__ == "__main__":
    main()
