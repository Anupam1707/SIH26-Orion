"""
predict_and_explain.py — Module 5 Tier 3: Inference + Evidence Subgraphs
=========================================================================
Runs the best Level 2 (ML classifier) and Level 3 (GNN embedder) models
over all candidate pairs in the graph to produce ranked link predictions
with attached evidence subgraphs.

Evidence subgraph per prediction
---------------------------------
  * Up to 3 shortest connecting paths through the training graph
  * Shared neighbors (with labels from entity CSVs)
  * Adamic-Adar / Resource Allocation / Jaccard subscores
  * Provenance tag: is_predicted=True

Ground truth recall check
--------------------------
  * Financial graph: checks whether mule chain edges (e.g. A00001→A00013)
    appear in the top-K predictions when held out.
  * Communication graph: checks whether BRIDGE_01 (PH04296↔PH04450) and
    BRIDGE_02 (PH02064↔PH04287) are recovered in top-50.

Outputs (intelligence/data/link_prediction/)
----------------------------------------
    predictions_{graph}.csv           — full ranked prediction list
    evidence_subgraphs_{graph}.json   — evidence for top-50 predictions
    ground_truth_recall_{graph}.txt   — bridge / mule edge recall report

Run
---
    python intelligence/link_prediction/predict_and_explain.py
    python intelligence/link_prediction/predict_and_explain.py --graph communication
    python intelligence/link_prediction/predict_and_explain.py --topk 100
"""

from __future__ import annotations

import argparse
import json
import math
import pickle
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import torch

LP_DIR = Path(__file__).resolve().parent.parent.parent / "intelligence" / "data" / "link_prediction"
DATA   = Path(__file__).resolve().parent.parent.parent / "data" / "dataset"

GRAPHS = {
    "financial":     ("source_account_id", "target_account_id"),
    "communication": ("source_phone_id",   "target_phone_id"),
}

# Ground truth bridges / mule edges we want to recover
GT_PAIRS = {
    "communication": [
        ("PH04296", "PH04450", "BRIDGE_01"),
        ("PH02064", "PH04287", "BRIDGE_02"),
    ],
    "financial": [
        ("A00001", "A00013", "MULE_01_feeder"),
        ("A00012", "A00013", "MULE_01_feeder"),
        ("A00013", "A00014", "MULE_01_collector"),
        ("A00043", "A00047", "LAYERING_01_chain"),
        ("A00069", "A00070", "STRUCTURING_01"),
    ],
}

CANDIDATE_CAP = 10_000   # max candidate pairs to score (feasibility)
TOP_K_EVIDENCE = 50


# ── candidate generation ───────────────────────────────────────────────────────

def _generate_candidates(G: nx.DiGraph,
                         held_out_edges: set[tuple],
                         graph_name: str) -> list[tuple]:
    """
    Generate candidate non-edges sorted by shared-neighbor count.
    ALWAYS includes held-out edges and known GT pairs so recall is measurable.
    Capped at CANDIDATE_CAP pairs (GT pairs are injected on top, not counted
    against the cap).
    """
    U = G.to_undirected()
    train_edges = set(U.edges())
    seen: set[tuple] = set()
    scored: list[tuple[int, str, str]] = []

    for node in list(U.nodes()):
        nbrs = set(U.neighbors(node))
        for nbr in nbrs:
            for fof in U.neighbors(nbr):
                if fof == node:
                    continue
                pair = (node, fof) if node < fof else (fof, node)
                if pair in seen:
                    continue
                if (node, fof) in train_edges or (fof, node) in train_edges:
                    continue
                cn = len(set(U.neighbors(node)) & set(U.neighbors(fof)))
                scored.append((cn, node, fof))
                seen.add(pair)

    scored.sort(reverse=True)
    result = [(u, v) for _, u, v in scored[:CANDIDATE_CAP]]

    # Inject held-out edges so recall is measurable
    result_set = {(u, v) for u, v in result} | {(v, u) for u, v in result}
    for u, v in held_out_edges:
        if (u, v) not in result_set and (v, u) not in result_set:
            if U.has_node(u) and U.has_node(v):
                result.append((u, v))
                result_set.add((u, v))

    # Inject known GT pairs (even if nodes are in different components)
    for gt_u, gt_v, _ in GT_PAIRS.get(graph_name, []):
        if (gt_u, gt_v) not in result_set and (gt_v, gt_u) not in result_set:
            if G.has_node(gt_u) and G.has_node(gt_v):
                result.append((gt_u, gt_v))
                result_set.add((gt_u, gt_v))

    return result


# ── feature builder for candidates ────────────────────────────────────────────

def _topo_score(U: nx.Graph, u: str, v: str) -> dict:
    cn = list(nx.common_neighbors(U, u, v))
    aa = sum(1.0 / math.log(U.degree(w)) for w in cn if U.degree(w) > 1)
    ra = sum(1.0 / U.degree(w) for w in cn if U.degree(w) > 0)
    nu, nv = set(U.neighbors(u)), set(U.neighbors(v))
    denom = len(nu | nv)
    jac = len(nu & nv) / denom if denom else 0.0
    pa  = float(U.degree(u) * U.degree(v))
    try:
        spl = nx.shortest_path_length(U, u, v)
    except Exception:
        spl = 6
    return {
        "common_neighbors": float(len(cn)),
        "adamic_adar": aa,
        "resource_allocation": ra,
        "jaccard": jac,
        "preferential_attachment": pa,
        "shortest_path_len": float(min(spl, 6)),
        "n_paths_2hop": float(len(cn)),
        "n_paths_3hop": 0.0,
    }


# ── evidence subgraph builder ─────────────────────────────────────────────────

def _build_evidence(G: nx.DiGraph, U: nx.Graph,
                    u: str, v: str,
                    entity_labels: dict) -> dict:
    """Build a human-readable evidence subgraph for a predicted link."""
    # shortest paths
    paths = []
    try:
        for path in list(nx.all_simple_paths(U, u, v, cutoff=4))[:3]:
            paths.append(path)
    except Exception:
        pass

    # shared neighbors
    shared = list(nx.common_neighbors(U, u, v))

    # topo subscores
    topo = _topo_score(U, u, v)

    return {
        "src": u,
        "dst": v,
        "is_predicted": True,
        "confidence_tier": "PREDICTED",
        "adamic_adar": round(topo["adamic_adar"], 4),
        "resource_allocation": round(topo["resource_allocation"], 4),
        "jaccard": round(topo["jaccard"], 4),
        "common_neighbors_count": len(shared),
        "shared_neighbors": shared[:10],
        "shared_neighbor_labels": [entity_labels.get(n, "unknown") for n in shared[:10]],
        "connecting_paths": paths,
        "path_count": len(paths),
    }


# ── entity label lookup ───────────────────────────────────────────────────────

def _load_entity_labels(graph_name: str) -> dict:
    labels: dict[str, str] = {}
    if graph_name == "financial":
        try:
            acc = pd.read_csv(DATA / "ENTITIES" / "accounts.csv")
            id_col = "account_id" if "account_id" in acc.columns else acc.columns[0]
            for _, row in acc.iterrows():
                aid = str(row[id_col])
                labels[aid] = f"Account({aid})"
        except Exception:
            pass
    else:
        try:
            phones = pd.read_csv(DATA / "ENTITIES" / "phone_numbers.csv")
            id_col = "phone_id" if "phone_id" in phones.columns else phones.columns[0]
            owner_col = "owner_person_id" if "owner_person_id" in phones.columns else None
            for _, row in phones.iterrows():
                pid = str(row[id_col])
                owner = str(row[owner_col]) if owner_col else "?"
                labels[pid] = f"Phone({pid}, owner={owner})"
        except Exception:
            pass
    return labels


# ── ground truth recall ───────────────────────────────────────────────────────

def _check_gt_recall(ranked_df: pd.DataFrame,
                     src_col: str, dst_col: str,
                     graph_name: str, top_k: int = 50) -> str:
    gt_pairs = GT_PAIRS.get(graph_name, [])
    top_df   = ranked_df.head(top_k)

    lines = [f"Ground Truth Recall @ top-{top_k}  [{graph_name}]",
             "=" * 55]
    for u, v, label in gt_pairs:
        in_top = (
            ((top_df[src_col] == u) & (top_df[dst_col] == v)) |
            ((top_df[src_col] == v) & (top_df[dst_col] == u))
        ).any()
        rank = None
        for i, row in ranked_df.iterrows():
            if (row[src_col] == u and row[dst_col] == v) or \
               (row[src_col] == v and row[dst_col] == u):
                rank = i + 1
                break
        status = "✅ RECOVERED" if in_top else f"❌ rank={rank or '>'+str(len(ranked_df))}"
        lines.append(f"  {label:<30} {u} ↔ {v}  →  {status}")

    return "\n".join(lines)


# ── level 2 scoring (ML classifier) ──────────────────────────────────────────

def _score_with_classifier(candidates: list[tuple], graph_name: str,
                            U: nx.Graph, node_feats_pkl: dict | None) -> np.ndarray | None:
    model_path = LP_DIR / f"best_model_{graph_name}.pkl"
    if not model_path.exists():
        print("  Level 2 model not found — skipping ML scores.")
        return None

    with open(model_path, "rb") as f:
        bundle = pickle.load(f)
    clf = bundle["model"]
    feature_names: list[str] = bundle["feature_names"]

    src_col, dst_col = GRAPHS[graph_name]

    rows = []
    for u, v in candidates:
        topo = _topo_score(U, u, v)
        row  = {k: topo.get(k, 0.0) for k in feature_names if k in topo}
        # fill missing features with 0
        for fn in feature_names:
            if fn not in row:
                row[fn] = 0.0
        rows.append([row[fn] for fn in feature_names])

    X = np.array(rows, dtype=np.float64)
    return clf.predict_proba(X)[:, 1]


# ── level 3 scoring (GNN) ────────────────────────────────────────────────────

def _score_with_gnn(candidates: list[tuple], graph_name: str) -> np.ndarray | None:
    meta_path = LP_DIR / f"gnn_model_meta_{graph_name}.json"
    model_path = LP_DIR / f"gnn_model_{graph_name}.pt"
    emb_path   = LP_DIR / f"node_embeddings_{graph_name}.npy"
    idx_path   = LP_DIR / f"node_index_{graph_name}.json"

    if not all(p.exists() for p in [meta_path, model_path, emb_path, idx_path]):
        print("  Level 3 GNN model not found — skipping GNN scores.")
        return None

    meta     = json.loads(meta_path.read_text())
    emb      = np.load(emb_path)
    node2idx = json.loads(idx_path.read_text())

    import importlib.util, sys
    _spec = importlib.util.spec_from_file_location(
        "gnn_embedder",
        Path(__file__).parent / "gnn_embedder.py"
    )
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    _LinkMLP = _mod._LinkMLP
    mlp = _LinkMLP(meta["embed_dim"], meta["mlp_hidden"])
    mlp.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
    mlp.eval()

    rows = []
    for u, v in candidates:
        eu = emb[node2idx[u]] if u in node2idx else np.zeros(meta["embed_dim"])
        ev = emb[node2idx[v]] if v in node2idx else np.zeros(meta["embed_dim"])
        rows.append(eu * ev)

    X = torch.tensor(np.array(rows, dtype=np.float32))
    with torch.no_grad():
        scores = torch.sigmoid(mlp(X)).numpy()
    return scores


# ── main ───────────────────────────────────────────────────────────────────────

def run_graph(graph_name: str, top_k: int = TOP_K_EVIDENCE) -> None:
    src_col, dst_col = GRAPHS[graph_name]

    graph_path = LP_DIR / f"graph_train_{graph_name}.pkl"
    if not graph_path.exists():
        print(f"Training graph missing — run dataset_builder.py first.")
        return

    with open(graph_path, "rb") as f:
        train_G: nx.DiGraph = pickle.load(f)
    U = train_G.to_undirected()

    entity_labels = _load_entity_labels(graph_name)

    # build held-out edge set (val + test positives = edges we removed from training)
    held_out: set[tuple] = set()
    for split in ("val", "test"):
        p = LP_DIR / f"{split}_pos_{graph_name}.csv"
        if p.exists():
            df_held = pd.read_csv(p)
            for _, r in df_held.iterrows():
                held_out.add((str(r[src_col]), str(r[dst_col])))

    print(f"\n── {graph_name} graph ──")
    print(f"  Held-out edges: {len(held_out)}")
    print(f"  Generating candidates (cap={CANDIDATE_CAP} + held-out + GT pairs) …")
    candidates = _generate_candidates(train_G, held_out, graph_name)
    print(f"  {len(candidates)} candidate pairs")

    # score with both models; use ensemble only if GNN beats or matches RF
    clf_scores = _score_with_classifier(candidates, graph_name, U, None)
    gnn_scores = _score_with_gnn(candidates, graph_name)

    # Read GNN and RF val AUCs to decide whether to ensemble
    use_gnn = False
    if gnn_scores is not None:
        meta_path = LP_DIR / f"gnn_model_meta_{graph_name}.json"
        clf_results_path = LP_DIR / f"clf_results_{graph_name}.csv"
        try:
            import json, pandas as _pd
            gnn_meta = json.loads(meta_path.read_text())
            gnn_val_auc = gnn_meta.get("val_auc", 0.0)
            clf_df = _pd.read_csv(clf_results_path)
            best_clf_val = clf_df[clf_df["split"] == "val"]["auc"].max()
            use_gnn = gnn_val_auc >= best_clf_val
            print(f"  GNN val_AUC={gnn_val_auc:.4f}  RF val_AUC={best_clf_val:.4f}  "
                  f"  → {'ensemble' if use_gnn else 'classifier-only'}")
        except Exception:
            use_gnn = False

    # ensemble: average available scores only if GNN is competitive
    if clf_scores is not None and gnn_scores is not None and use_gnn:
        ensemble = (clf_scores + gnn_scores) / 2.0
        model_tag = "ensemble"
    elif clf_scores is not None:
        ensemble = clf_scores
        model_tag = "classifier"
    elif gnn_scores is not None:
        ensemble = gnn_scores
        model_tag = "gnn"
    else:
        # fall back to pure Adamic-Adar
        print("  No trained models found — using Adamic-Adar as fallback score.")
        ensemble = np.array([_topo_score(U, u, v)["adamic_adar"] for u, v in candidates])
        model_tag = "adamic_adar_fallback"

    # build predictions DataFrame
    preds_df = pd.DataFrame({
        src_col: [u for u, _ in candidates],
        dst_col: [v for _, v in candidates],
        "score": ensemble,
        "model": model_tag,
        "is_predicted": True,
    }).sort_values("score", ascending=False).reset_index(drop=True)
    preds_df["rank"] = preds_df.index + 1

    # add topo subscores
    topo_cols = ["common_neighbors", "adamic_adar", "resource_allocation", "jaccard"]
    topo_rows = [_topo_score(U, u, v) for u, v in zip(preds_df[src_col], preds_df[dst_col])]
    for col in topo_cols:
        preds_df[col] = [r[col] for r in topo_rows]

    preds_path = LP_DIR / f"predictions_{graph_name}.csv"
    preds_df.to_csv(preds_path, index=False)
    print(f"  Predictions saved → {preds_path.name}  ({len(preds_df)} rows)")

    # ── evidence subgraphs for top-K ──
    print(f"  Building evidence subgraphs for top-{top_k} …")
    evidence = []
    for _, row in preds_df.head(top_k).iterrows():
        ev = _build_evidence(train_G, U, str(row[src_col]), str(row[dst_col]), entity_labels)
        ev["rank"]  = int(row["rank"])
        ev["score"] = float(row["score"])
        evidence.append(ev)

    ev_path = LP_DIR / f"evidence_subgraphs_{graph_name}.json"
    ev_path.write_text(json.dumps(evidence, indent=2))
    print(f"  Evidence subgraphs saved → {ev_path.name}")

    # ── ground truth recall ──
    recall_report = _check_gt_recall(preds_df, src_col, dst_col, graph_name, top_k)
    print("\n" + recall_report)
    recall_path = LP_DIR / f"ground_truth_recall_{graph_name}.txt"
    recall_path.write_text(recall_report)

    # print top-10 predictions
    print(f"\n  Top-10 predicted links [{graph_name}]:")
    print(f"  {'Rank':<6} {src_col:<16} {dst_col:<16} {'Score':>8} {'AA':>8} {'CN':>6}")
    print("  " + "-" * 64)
    for _, row in preds_df.head(10).iterrows():
        print(f"  {int(row['rank']):<6} {str(row[src_col]):<16} {str(row[dst_col]):<16} "
              f"{row['score']:>8.4f} {row['adamic_adar']:>8.4f} {int(row['common_neighbors']):>6}")


def main(graphs: list[str] | None = None, top_k: int = TOP_K_EVIDENCE) -> None:
    if graphs is None:
        graphs = list(GRAPHS.keys())

    print("=" * 60)
    print("Module 5 Tier 3 — Inference + Evidence Subgraphs")
    print("=" * 60)

    for g in graphs:
        run_graph(g, top_k=top_k)

    print("\nAll done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", choices=list(GRAPHS.keys()))
    parser.add_argument("--topk", type=int, default=TOP_K_EVIDENCE)
    args = parser.parse_args()
    main(graphs=[args.graph] if args.graph else None, top_k=args.topk)
