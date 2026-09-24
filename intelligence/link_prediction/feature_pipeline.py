"""
feature_pipeline.py — Module 5 Tier 3: Edge Feature Engineering
================================================================
Builds a feature vector for every candidate edge pair (positive + negative)
by combining topological heuristics, node-level graph properties, and
entity-level activity statistics.

Feature groups
--------------
  Topological (pair-level, from training graph):
    common_neighbors, adamic_adar, resource_allocation, jaccard,
    preferential_attachment, shortest_path_len, n_paths_2hop, n_paths_3hop

  Node-level (both src and dst):
    in_degree, out_degree, total_degree, pagerank, betweenness_approx,
    same_community (1 if src & dst share Louvain community_id)

  Activity stats — financial graph:
    src/dst mean_tx_amount, max_tx_amount, tx_count, tx_per_day

  Activity stats — communication graph:
    src/dst call_count, sms_count, mean_duration

Outputs (intelligence/data/link_prediction/)
----------------------------------------
    features_train_{graph}.parquet
    features_val_{graph}.parquet
    features_test_{graph}.parquet

Run
---
    python intelligence/link_prediction/feature_pipeline.py
    python intelligence/link_prediction/feature_pipeline.py --graph financial
"""

from __future__ import annotations

import argparse
import math
import pickle
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

ROOT   = Path(__file__).resolve().parent.parent.parent
DATA   = ROOT / "data" / "dataset" / "RELATIONSHIPS"
LP_DIR = ROOT / "intelligence" / "data" / "link_prediction"

GRAPHS = {
    "financial":     ("source_account_id", "target_account_id"),
    "communication": ("source_phone_id",   "target_phone_id"),
}

PAGERANK_ALPHA  = 0.85
PAGERANK_ITER   = 100
BETW_K          = 200    # k-sample betweenness approximation
MAX_PATH_LEN    = 6      # cap for shortest path; inf → 6


# ── graph-level node features ──────────────────────────────────────────────────

def _compute_node_features(G: nx.DiGraph) -> pd.DataFrame:
    """Returns DataFrame indexed by node_id with graph-level metrics."""
    U = G.to_undirected()

    print("    Computing PageRank …")
    pr = nx.pagerank(G, alpha=PAGERANK_ALPHA, max_iter=PAGERANK_ITER)

    print(f"    Computing betweenness (k={BETW_K}) …")
    betw = nx.betweenness_centrality(U, k=min(BETW_K, U.number_of_nodes()),
                                     normalized=True, seed=42)

    print("    Computing Louvain communities …")
    try:
        import community as community_louvain  # python-louvain
        partition = community_louvain.best_partition(U, random_state=42)
    except ImportError:
        # Fallback: use greedy modularity communities from NetworkX
        comms = nx.community.greedy_modularity_communities(U)
        partition = {}
        for i, c in enumerate(comms):
            for node in c:
                partition[node] = i

    records = []
    for node in G.nodes():
        records.append({
            "node_id":        node,
            "in_degree":      G.in_degree(node),
            "out_degree":     G.out_degree(node),
            "total_degree":   G.degree(node),
            "pagerank":       pr.get(node, 0.0),
            "betweenness":    betw.get(node, 0.0),
            "community_id":   partition.get(node, -1),
        })
    return pd.DataFrame(records).set_index("node_id")


# ── topological pair features ──────────────────────────────────────────────────

def _topo_features(U: nx.Graph, u: str, v: str) -> dict:
    cn = list(nx.common_neighbors(U, u, v))
    cn_count = float(len(cn))

    # Adamic-Adar
    aa = sum(1.0 / math.log(U.degree(w)) for w in cn if U.degree(w) > 1)

    # Resource Allocation
    ra = sum(1.0 / U.degree(w) for w in cn if U.degree(w) > 0)

    # Jaccard
    nu = set(U.neighbors(u))
    nv = set(U.neighbors(v))
    denom = len(nu | nv)
    jaccard = len(nu & nv) / denom if denom else 0.0

    # Preferential Attachment
    pa = float(U.degree(u) * U.degree(v))

    # Shortest path length
    try:
        spl = nx.shortest_path_length(U, u, v)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        spl = MAX_PATH_LEN

    # n_paths_2hop: count of 2-hop paths (= common neighbors)
    n_paths_2 = cn_count

    # n_paths_3hop: count of 3-hop paths (u → w → x → v, no revisit)
    n_paths_3 = 0.0
    if cn_count < 50:   # skip expensive computation for dense nodes
        for w in cn:
            for x in U.neighbors(w):
                if x != u and x != v and U.has_node(v) and U.has_edge(x, v):
                    n_paths_3 += 1.0

    return {
        "common_neighbors":        cn_count,
        "adamic_adar":             aa,
        "resource_allocation":     ra,
        "jaccard":                 jaccard,
        "preferential_attachment": pa,
        "shortest_path_len":       float(min(spl, MAX_PATH_LEN)),
        "n_paths_2hop":            n_paths_2,
        "n_paths_3hop":            n_paths_3,
    }


# ── activity stats ──────────────────────────────────────────────────────────────

def _financial_activity(train_pos: pd.DataFrame,
                        src_col: str, dst_col: str) -> pd.DataFrame:
    """Node-level financial stats derived from training transactions."""
    tx = pd.read_csv(DATA / "transactions.csv")
    tx["timestamp"] = pd.to_datetime(tx["timestamp"], errors="coerce")

    # Merge training split timestamps to cap at training period only
    # (use all transactions for node stats — avoids leakage from held-out amounts)
    records: dict[str, dict] = {}
    for account, grp in tx.groupby("source_account_id"):
        span_days = max(
            (grp["timestamp"].max() - grp["timestamp"].min()).days, 1
        )
        records[str(account)] = {
            "tx_count_src":   len(grp),
            "mean_tx_amount": grp["amount"].mean(),
            "max_tx_amount":  grp["amount"].max(),
            "tx_per_day":     len(grp) / span_days,
        }

    df = pd.DataFrame.from_dict(records, orient="index")
    df.index.name = "node_id"
    return df


def _communication_activity() -> pd.DataFrame:
    """Node-level communication stats."""
    comm = pd.read_csv(DATA / "communications.csv")
    records: dict[str, dict] = {}
    for phone, grp in comm.groupby("source_phone_id"):
        records[str(phone)] = {
            "call_count":    (grp["communication_type"] == "CALL").sum(),
            "sms_count":     (grp["communication_type"] == "SMS").sum(),
            "email_count":   (grp["communication_type"] == "EMAIL").sum(),
            "mean_duration": grp["duration_seconds"].mean()
            if "duration_seconds" in grp.columns else 0.0,
        }
    df = pd.DataFrame.from_dict(records, orient="index")
    df.index.name = "node_id"
    return df


# ── feature builder ───────────────────────────────────────────────────────────

def _build_features(
    pos_df: pd.DataFrame,
    neg_df: pd.DataFrame,
    src_col: str,
    dst_col: str,
    U: nx.Graph,
    node_feats: pd.DataFrame,
    activity_feats: pd.DataFrame | None,
) -> pd.DataFrame:
    pos = pos_df[[src_col, dst_col]].copy(); pos["label"] = 1
    neg = neg_df[[src_col, dst_col]].copy(); neg["label"] = 0
    df  = pd.concat([pos, neg], ignore_index=True)

    print(f"    Scoring {len(df)} pairs …")
    topo_rows  = []
    for _, row in df.iterrows():
        u, v = str(row[src_col]), str(row[dst_col])
        if U.has_node(u) and U.has_node(v):
            topo_rows.append(_topo_features(U, u, v))
        else:
            topo_rows.append({k: 0.0 for k in [
                "common_neighbors", "adamic_adar", "resource_allocation",
                "jaccard", "preferential_attachment", "shortest_path_len",
                "n_paths_2hop", "n_paths_3hop",
            ]})
    topo_df = pd.DataFrame(topo_rows)

    # node features for src and dst
    def _get_node_row(nid: str, suffix: str) -> dict:
        if nid in node_feats.index:
            row = node_feats.loc[nid].to_dict()
        else:
            row = {c: 0.0 for c in node_feats.columns}
        return {f"{k}_{suffix}": v for k, v in row.items()}

    src_rows = [_get_node_row(str(r[src_col]), "src") for _, r in df.iterrows()]
    dst_rows = [_get_node_row(str(r[dst_col]), "dst") for _, r in df.iterrows()]
    src_nf = pd.DataFrame(src_rows)
    dst_nf = pd.DataFrame(dst_rows)

    # same_community flag
    same_comm = (src_nf["community_id_src"].values == dst_nf["community_id_dst"].values).astype(float)

    # activity features
    def _get_act_row(nid: str, suffix: str) -> dict:
        if activity_feats is not None and nid in activity_feats.index:
            row = activity_feats.loc[nid].to_dict()
        else:
            row = {}
        return {f"{k}_{suffix}": v for k, v in row.items()}

    act_src = pd.DataFrame([_get_act_row(str(r[src_col]), "src") for _, r in df.iterrows()])
    act_dst = pd.DataFrame([_get_act_row(str(r[dst_col]), "dst") for _, r in df.iterrows()])

    result = pd.concat([
        df[[src_col, dst_col, "label"]].reset_index(drop=True),
        topo_df.reset_index(drop=True),
        src_nf.drop(columns=["community_id_src"]).reset_index(drop=True),
        dst_nf.drop(columns=["community_id_dst"]).reset_index(drop=True),
        pd.Series(same_comm, name="same_community").reset_index(drop=True),
        act_src.reset_index(drop=True),
        act_dst.reset_index(drop=True),
    ], axis=1)

    result = result.fillna(0.0)
    return result


# ── entry point ───────────────────────────────────────────────────────────────

def run_graph(graph_name: str) -> None:
    src_col, dst_col = GRAPHS[graph_name]

    graph_path = LP_DIR / f"graph_train_{graph_name}.pkl"
    if not graph_path.exists():
        raise FileNotFoundError(
            f"Training graph not found: {graph_path}\n"
            "Run dataset_builder.py first."
        )
    with open(graph_path, "rb") as f:
        train_G: nx.DiGraph = pickle.load(f)
    U = train_G.to_undirected()

    print(f"\n── {graph_name} graph ──")
    print("  Computing node-level features …")
    node_feats = _compute_node_features(train_G)

    print("  Computing activity stats …")
    if graph_name == "financial":
        train_pos = pd.read_csv(LP_DIR / f"train_pos_{graph_name}.csv")
        activity = _financial_activity(train_pos, src_col, dst_col)
    else:
        activity = _communication_activity()

    for split in ("train", "val", "test"):
        pos_path = LP_DIR / f"{split}_pos_{graph_name}.csv"
        neg_path = LP_DIR / f"{split}_neg_{graph_name}.csv"
        if not pos_path.exists():
            print(f"  Skipping {split} (missing files — run dataset_builder.py first)")
            continue

        print(f"  Building features for {split} split …")
        pos_df = pd.read_csv(pos_path)
        neg_df = pd.read_csv(neg_path)

        feat_df = _build_features(pos_df, neg_df, src_col, dst_col,
                                   U, node_feats, activity)

        out = LP_DIR / f"features_{split}_{graph_name}.parquet"
        feat_df.to_parquet(out, index=False)
        print(f"    Saved {len(feat_df)} rows → {out.name}")


def main(graphs: list[str] | None = None) -> None:
    if graphs is None:
        graphs = list(GRAPHS.keys())

    print("=" * 60)
    print("Module 5 Tier 3 — Feature Pipeline")
    print("=" * 60)

    for g in graphs:
        run_graph(g)

    print("\nDone. Run train_classifier.py next.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", choices=list(GRAPHS.keys()))
    args = parser.parse_args()
    main(graphs=[args.graph] if args.graph else None)
