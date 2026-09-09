"""
gnn_embedder.py — Module 5 Tier 3: Level 3 PyTorch Node2Vec Embeddings
=======================================================================
Learns 64-dimensional node embeddings via Node2Vec (biased random walks +
Skip-Gram) using pure PyTorch + NetworkX — no torch_geometric required.

Architecture
------------
  1. Biased random walks (p, q parameters) sampled from training graph.
  2. Skip-Gram word2vec model trained to produce node embeddings.
  3. Link prediction head: Hadamard(emb_u, emb_v) → 2-layer MLP → sigmoid.
  4. Training: BCEWithLogitsLoss on train positives + negatives.
  5. Early stopping on val AUC-ROC.

Outputs (module5/data/link_prediction/)
----------------------------------------
    node_embeddings_{graph}.npy      — float32 array [n_nodes × dim]
    node_index_{graph}.json          — {node_id: row_index}
    gnn_results_{graph}.csv          — val + test AUC, AP per epoch

Run
---
    python module5/link_prediction/gnn_embedder.py
    python module5/link_prediction/gnn_embedder.py --graph financial --epochs 30
"""

from __future__ import annotations

import argparse
import json
import pickle
import random
from collections import defaultdict
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT   = Path(__file__).resolve().parent.parent.parent
LP_DIR = ROOT / "module5" / "data" / "link_prediction"

GRAPHS = {
    "financial":     ("source_account_id", "target_account_id"),
    "communication": ("source_phone_id",   "target_phone_id"),
}

# ── hyper-parameters (kept intentionally modest for CPU training) ─────────────
EMBED_DIM     = 64
WALK_LENGTH   = 20
WALKS_PER_NODE = 10
WINDOW_SIZE   = 5
P             = 1.0    # return parameter (breadth-first bias)
Q             = 1.0    # in-out parameter (depth-first bias); 1 = unbiased
SKIPGRAM_EPOCHS = 5
SKIPGRAM_LR   = 0.025
MLP_HIDDEN    = 64
MLP_EPOCHS    = 50
MLP_LR        = 1e-3
BATCH_SIZE    = 256
PATIENCE      = 5       # early stopping patience on val AUC
LABEL_COL     = "label"
RANDOM_SEED   = 42


# ── biased random walk ─────────────────────────────────────────────────────────

def _compute_alias(probs: list[float]):
    """Vose's alias method for O(1) sampling."""
    n = len(probs)
    q_arr = np.array(probs, dtype=np.float64) * n
    J = np.zeros(n, dtype=int)
    smaller, larger = [], []
    for i, q in enumerate(q_arr):
        (smaller if q < 1.0 else larger).append(i)
    while smaller and larger:
        s = smaller.pop()
        l = larger.pop()
        J[s] = l
        q_arr[l] = q_arr[l] + q_arr[s] - 1.0
        (smaller if q_arr[l] < 1.0 else larger).append(l)
    return J, q_arr


def _alias_draw(J, q):
    n = len(J)
    idx = random.randint(0, n - 1)
    return idx if random.random() < q[idx] else J[idx]


def _node2vec_walks(G: nx.DiGraph,
                    walk_length: int,
                    walks_per_node: int,
                    p: float, q: float,
                    seed: int = RANDOM_SEED) -> list[list[str]]:
    """Generate biased random walks for Node2Vec."""
    random.seed(seed)
    U = G.to_undirected()
    nodes = list(U.nodes())

    # precompute alias tables per (prev, curr) edge transition
    alias: dict[tuple, tuple] = {}

    def _edge_probs(prev: str | None, curr: str) -> list[float]:
        nbrs = list(U.neighbors(curr))
        weights = []
        for nbr in nbrs:
            if nbr == prev:
                weights.append(1.0 / p)
            elif U.has_edge(prev, nbr) if prev is not None else False:
                weights.append(1.0)
            else:
                weights.append(1.0 / q)
        s = sum(weights)
        return [w / s for w in weights]

    print(f"    Precomputing alias tables for {U.number_of_edges()} edges …")
    for node in U.nodes():
        nbrs = list(U.neighbors(node))
        if not nbrs:
            continue
        # first-step (no previous)
        uniform = [1.0 / len(nbrs)] * len(nbrs)
        alias[(None, node)] = (_compute_alias(uniform), nbrs)
        # per-edge
        for nbr in nbrs:
            nbrs2 = list(U.neighbors(nbr))
            if not nbrs2:
                continue
            probs = _edge_probs(node, nbr)
            alias[(node, nbr)] = (_compute_alias(probs), nbrs2)

    print(f"    Generating {walks_per_node * len(nodes)} random walks …")
    all_walks: list[list[str]] = []
    for _ in range(walks_per_node):
        random.shuffle(nodes)
        for start in nodes:
            walk = [start]
            if (None, start) not in alias:
                continue
            for _ in range(walk_length - 1):
                curr = walk[-1]
                prev = walk[-2] if len(walk) > 1 else None
                key  = (prev, curr)
                if key not in alias:
                    break
                (J, q_table), nbrs = alias[key]
                nxt = nbrs[_alias_draw(J, q_table)]
                walk.append(nxt)
            all_walks.append(walk)

    return all_walks


# ── skip-gram embeddings ───────────────────────────────────────────────────────

class _SkipGram(nn.Module):
    def __init__(self, n_nodes: int, embed_dim: int):
        super().__init__()
        self.embeddings = nn.Embedding(n_nodes, embed_dim)
        self.context    = nn.Embedding(n_nodes, embed_dim)
        nn.init.xavier_uniform_(self.embeddings.weight)
        nn.init.zeros_(self.context.weight)

    def forward(self, center: torch.Tensor, context: torch.Tensor) -> torch.Tensor:
        e_c = self.embeddings(center)           # [B, D]
        e_x = self.context(context)             # [B, D]
        return (e_c * e_x).sum(dim=-1)          # [B]


def _train_skipgram(walks: list[list[str]], node2idx: dict,
                    embed_dim: int, epochs: int, lr: float) -> np.ndarray:
    n = len(node2idx)
    model = _SkipGram(n, embed_dim)
    opt   = optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.BCEWithLogitsLoss()

    # build (center, context) pairs
    pairs = []
    for walk in walks:
        idx_walk = [node2idx[w] for w in walk if w in node2idx]
        for i, center in enumerate(idx_walk):
            lo = max(0, i - WINDOW_SIZE)
            hi = min(len(idx_walk), i + WINDOW_SIZE + 1)
            for j in range(lo, hi):
                if i != j:
                    pairs.append((center, idx_walk[j]))

    pairs = np.array(pairs, dtype=np.int64)
    print(f"    Skip-Gram: {len(pairs)} training pairs, {epochs} epochs …")

    for epoch in range(epochs):
        np.random.shuffle(pairs)
        total_loss = 0.0
        for start in range(0, len(pairs), BATCH_SIZE):
            batch = pairs[start: start + BATCH_SIZE]
            center  = torch.tensor(batch[:, 0])
            context = torch.tensor(batch[:, 1])

            # negative sampling (5 negs per positive)
            neg_ctx = torch.randint(0, n, (len(batch) * 5,))

            pos_score = model(center, context)
            neg_score = model(center.repeat_interleave(5), neg_ctx)

            pos_loss = loss_fn(pos_score, torch.ones_like(pos_score))
            neg_loss = loss_fn(neg_score, torch.zeros_like(neg_score))
            loss = pos_loss + neg_loss

            opt.zero_grad()
            loss.backward()
            opt.step()
            total_loss += loss.item()

        avg = total_loss / max(1, len(pairs) // BATCH_SIZE)
        print(f"      Epoch {epoch+1}/{epochs}  loss={avg:.4f}")

    embeddings = model.embeddings.weight.detach().cpu().numpy()
    return embeddings


# ── MLP link prediction head ───────────────────────────────────────────────────

class _LinkMLP(nn.Module):
    def __init__(self, in_dim: int, hidden: int = MLP_HIDDEN):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_dim, hidden),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def _hadamard(emb: np.ndarray, node2idx: dict,
              pairs_df: pd.DataFrame,
              src_col: str, dst_col: str) -> np.ndarray:
    """Hadamard product of embeddings for each edge pair."""
    rows = []
    for _, row in pairs_df.iterrows():
        u = str(row[src_col])
        v = str(row[dst_col])
        eu = emb[node2idx[u]] if u in node2idx else np.zeros(emb.shape[1])
        ev = emb[node2idx[v]] if v in node2idx else np.zeros(emb.shape[1])
        rows.append(eu * ev)
    return np.array(rows, dtype=np.float32)


def _train_mlp(X_train, y_train, X_val, y_val,
               X_test, y_test) -> tuple[dict, _LinkMLP]:
    device = torch.device("cpu")
    model  = _LinkMLP(X_train.shape[1]).to(device)
    opt    = optim.Adam(model.parameters(), lr=MLP_LR)
    loss_fn = nn.BCEWithLogitsLoss(
        pos_weight=torch.tensor([(y_train == 0).sum() / max((y_train == 1).sum(), 1)],
                                dtype=torch.float32)
    )

    Xt = torch.tensor(X_train, dtype=torch.float32)
    yt = torch.tensor(y_train, dtype=torch.float32)
    Xv = torch.tensor(X_val,   dtype=torch.float32)
    yv_np = y_val

    best_val_auc  = 0.0
    best_state    = None
    patience_cnt  = 0
    results       = []

    print(f"    MLP training {MLP_EPOCHS} epochs (early stop patience={PATIENCE}) …")
    for epoch in range(MLP_EPOCHS):
        model.train()
        perm = torch.randperm(len(Xt))
        ep_loss = 0.0
        for start in range(0, len(Xt), BATCH_SIZE):
            idx   = perm[start: start + BATCH_SIZE]
            logit = model(Xt[idx])
            loss  = loss_fn(logit, yt[idx])
            opt.zero_grad()
            loss.backward()
            opt.step()
            ep_loss += loss.item()

        model.eval()
        with torch.no_grad():
            val_score = torch.sigmoid(model(Xv)).numpy()

        try:
            val_auc = roc_auc_score(yv_np, val_score)
            val_ap  = average_precision_score(yv_np, val_score)
        except ValueError:
            val_auc = val_ap = float("nan")

        results.append({"epoch": epoch + 1, "val_auc": val_auc, "val_ap": val_ap})

        if epoch % 5 == 0 or epoch == MLP_EPOCHS - 1:
            print(f"      Epoch {epoch+1:3d}  loss={ep_loss:.3f}  val_auc={val_auc:.4f}")

        if val_auc > best_val_auc:
            best_val_auc = val_auc
            best_state   = {k: v.clone() for k, v in model.state_dict().items()}
            patience_cnt = 0
        else:
            patience_cnt += 1
            if patience_cnt >= PATIENCE:
                print(f"      Early stopping at epoch {epoch+1}")
                break

    # restore best
    model.load_state_dict(best_state)
    model.eval()

    Xte = torch.tensor(X_test, dtype=torch.float32)
    with torch.no_grad():
        test_score = torch.sigmoid(model(Xte)).numpy()
    try:
        test_auc = roc_auc_score(y_test, test_score)
        test_ap  = average_precision_score(y_test, test_score)
    except ValueError:
        test_auc = test_ap = float("nan")

    print(f"\n    Best val AUC={best_val_auc:.4f}  Test AUC={test_auc:.4f}  Test AP={test_ap:.4f}")
    return {"val_auc": best_val_auc, "test_auc": test_auc,
            "test_ap": test_ap, "epochs": results}, model


# ── entry point ───────────────────────────────────────────────────────────────

def run_graph(graph_name: str, epochs: int | None = None) -> None:
    src_col, dst_col = GRAPHS[graph_name]

    graph_path = LP_DIR / f"graph_train_{graph_name}.pkl"
    if not graph_path.exists():
        print(f"Training graph not found — run dataset_builder.py first.")
        return

    with open(graph_path, "rb") as f:
        train_G: nx.DiGraph = pickle.load(f)

    nodes    = list(train_G.nodes())
    node2idx = {n: i for i, n in enumerate(nodes)}
    print(f"\n── {graph_name} graph: {len(nodes)} nodes ──")

    # ── 1. generate random walks ──
    walks = _node2vec_walks(train_G, WALK_LENGTH, WALKS_PER_NODE, P, Q, RANDOM_SEED)

    # ── 2. skip-gram embeddings ──
    print("  Training Skip-Gram embeddings …")
    sg_epochs = epochs if epochs is not None else SKIPGRAM_EPOCHS
    emb = _train_skipgram(walks, node2idx, EMBED_DIM, sg_epochs, SKIPGRAM_LR)

    # save embeddings
    np.save(LP_DIR / f"node_embeddings_{graph_name}.npy", emb)
    (LP_DIR / f"node_index_{graph_name}.json").write_text(json.dumps(node2idx))
    print(f"  Embeddings saved: {emb.shape}")

    # ── 3. MLP link prediction head ──
    def _load_split(split):
        pos = pd.read_csv(LP_DIR / f"{split}_pos_{graph_name}.csv")
        neg = pd.read_csv(LP_DIR / f"{split}_neg_{graph_name}.csv")
        df  = pd.concat([
            pos[[src_col, dst_col]].assign(label=1),
            neg[[src_col, dst_col]].assign(label=0),
        ], ignore_index=True)
        X = _hadamard(emb, node2idx, df, src_col, dst_col)
        y = df["label"].values
        return X, y

    for split in ("train", "val", "test"):
        if not (LP_DIR / f"{split}_pos_{graph_name}.csv").exists():
            print(f"  Missing {split} split — run dataset_builder.py first.")
            return

    print("\n  Training MLP link prediction head …")
    X_train, y_train = _load_split("train")
    X_val,   y_val   = _load_split("val")
    X_test,  y_test  = _load_split("test")

    mlp_epochs = epochs if epochs is not None else MLP_EPOCHS
    results, mlp_model = _train_mlp(X_train, y_train, X_val, y_val, X_test, y_test)

    # save results
    results_df = pd.DataFrame(results["epochs"])
    results_df["graph"] = graph_name
    results_df.to_csv(LP_DIR / f"gnn_results_{graph_name}.csv", index=False)

    # save MLP model
    torch.save(mlp_model.state_dict(), LP_DIR / f"gnn_model_{graph_name}.pt")
    (LP_DIR / f"gnn_model_meta_{graph_name}.json").write_text(json.dumps({
        "embed_dim": EMBED_DIM, "mlp_hidden": MLP_HIDDEN,
        "graph": graph_name, "src_col": src_col, "dst_col": dst_col,
        "n_nodes": len(nodes),
        "val_auc": results["val_auc"],
        "test_auc": results["test_auc"],
        "test_ap": results["test_ap"],
    }, indent=2))


def main(graphs: list[str] | None = None, epochs: int | None = None) -> None:
    if graphs is None:
        graphs = list(GRAPHS.keys())
    torch.manual_seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)
    random.seed(RANDOM_SEED)

    print("=" * 60)
    print("Module 5 Tier 3 — Level 3 Node2Vec + MLP Link Predictor")
    print("=" * 60)

    for g in graphs:
        run_graph(g, epochs=epochs)

    print("\nDone. Run predict_and_explain.py next.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", choices=list(GRAPHS.keys()))
    parser.add_argument("--epochs", type=int, help="Override training epochs")
    args = parser.parse_args()
    main(graphs=[args.graph] if args.graph else None, epochs=args.epochs)
