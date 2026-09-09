"""
Module 5 — Tier 3: Link Prediction
====================================
Package init. Exposes a run_all() convenience wrapper that runs
the full pipeline end-to-end for a given graph.

Usage:
    from module5.link_prediction import run_all
    run_all("financial")
    run_all("communication")

Or from CLI (running each script individually gives more control):
    python module5/link_prediction/dataset_builder.py
    python module5/link_prediction/heuristics.py
    python module5/link_prediction/feature_pipeline.py
    python module5/link_prediction/train_classifier.py
    python module5/link_prediction/gnn_embedder.py
    python module5/link_prediction/predict_and_explain.py
"""

from __future__ import annotations


def run_all(graph: str = "financial", skip_gnn: bool = False) -> None:
    """
    Run the full Tier 3 link prediction pipeline for one graph.

    Parameters
    ----------
    graph : "financial" | "communication"
    skip_gnn : bool
        If True, skips the Node2Vec GNN step (much faster, useful for smoke tests).
    """
    from . import dataset_builder, heuristics, feature_pipeline, train_classifier, predict_and_explain

    print(f"\n{'='*60}")
    print(f"Module 5 Tier 3 — Full Pipeline  [{graph}]")
    print(f"{'='*60}")

    dataset_builder.main(graphs=[graph])
    heuristics.main(graphs=[graph])
    feature_pipeline.main(graphs=[graph])
    train_classifier.main(graphs=[graph])

    if not skip_gnn:
        from . import gnn_embedder
        gnn_embedder.main(graphs=[graph])

    predict_and_explain.main(graphs=[graph])
    print(f"\nPipeline complete for [{graph}].")


__all__ = ["run_all"]
