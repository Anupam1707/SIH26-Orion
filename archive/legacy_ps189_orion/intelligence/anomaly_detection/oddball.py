"""
Module 5 — Phase 2: Structural Anomaly Detection (OddBall)
===========================================================
OddBall method (Akoglu et al. 2010):
  In normal networks, egonet_edges ≈ C * egonet_nodes^alpha (power law).
  Accounts that deviate strongly from the fitted power law are structurally
  anomalous.  Deviation *below* expectation → STAR (mule-like hub).
  Deviation *above* expectation → NEAR_CLIQUE (fraud-cell-like dense group).

Input:  ../data/inputs/egonet_data.csv   (exported from Aura — see Cypher below)
Output: ../data/results/oddball_results.csv

Aura export Cypher (run once to refresh egonet_data.csv):
  MATCH (a:Account)
  OPTIONAL MATCH (a)-[:TRANSACTED]-(neighbour:Account)
  WITH a,
       collect(DISTINCT neighbour) AS neighbours,
       sum(CASE WHEN (a)-[:TRANSACTED]->(neighbour) THEN 1 ELSE 0 END) AS out_deg,
       sum(CASE WHEN (neighbour)-[:TRANSACTED]->(a) THEN 1 ELSE 0 END) AS in_deg
  ...
  (see project docs for full query)

Known limitations (documented in project log Section 8.3):
  - OddBall is structurally blind to *temporal* fraud (structuring, mule fan-in).
  - Accounts with zero internal egonet edges are excluded (no measurable shape).
  - The raw score was biased toward cliques; fixed by within-shape z-normalisation.
"""

from pathlib import Path
import pandas as pd
import numpy as np

# ── paths ─────────────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent
INPUT  = BASE / "../data/inputs/egonet_data.csv"
OUTPUT = BASE / "../data/results/oddball_results.csv"

# ── load ──────────────────────────────────────────────────────────────────────
df = pd.read_csv(INPUT)

# ── OddBall core: fit power-law in log-log space ──────────────────────────────
# Filter to accounts that actually have a measurable egonet shape.
d = df[(df.egonet_nodes > 1) & (df.egonet_edges > 0)].copy()

log_n = np.log10(d.egonet_nodes)
log_e = np.log10(d.egonet_edges)

alpha, intercept = np.polyfit(log_n, log_e, 1)
print(f"Fitted power law: edges = {10**intercept:.3f} * nodes^{alpha:.3f}")
print(f"Accounts scored: {len(d)} of {len(df)} total\n")

expected_log_e = alpha * log_n + intercept
d['expected_edges'] = 10 ** expected_log_e

# Raw OddBall outlier score: penalises deviation in either direction.
ratio = np.maximum(d.egonet_edges, d.expected_edges) / \
        np.minimum(d.egonet_edges, d.expected_edges)
d['oddball_score'] = ratio * np.log10(np.abs(d.egonet_edges - d.expected_edges) + 1)

# ── shape classification ──────────────────────────────────────────────────────
# fewer edges than expected  → STAR   (hub with unconnected spokes = mule-like)
# more edges than expected   → CLIQUE (everyone connected = fraud cell)
d['ego_shape'] = np.where(d.egonet_edges < d.expected_edges, 'STAR', 'NEAR_CLIQUE')

# ── shape-normalised score ────────────────────────────────────────────────────
# The raw score is biased toward cliques: with a low power-law exponent (α≈0.477),
# deviating *above* expectation scores much higher than deviating *below* it.
# Normalising within each shape category lets stars compete fairly against stars.
d['shape_norm_score'] = d.groupby('ego_shape')['oddball_score'].transform(
    lambda s: (s - s.mean()) / s.std()
)

# ── volume features ───────────────────────────────────────────────────────────
d['total_volume'] = d.in_volume + d.out_volume
d['total_deg']    = d.in_deg + d.out_deg
d['volume_per_tx'] = d.total_volume / d.total_deg.replace(0, np.nan)

result = d.sort_values('shape_norm_score', ascending=False).reset_index(drop=True)

cols = ['account_id', 'egonet_nodes', 'egonet_edges', 'expected_edges',
        'shape_norm_score', 'oddball_score', 'ego_shape']

print("=== TOP 20 STRUCTURAL ANOMALIES (shape-normalised) ===")
print(result[cols].head(20).to_string(index=False))
print(f"\nShape breakdown: {result.ego_shape.value_counts().to_dict()}")

# ── top STARs: mule-like structures ──────────────────────────────────────────
stars = result[result.ego_shape == 'STAR'].head(10)
if len(stars):
    print("\n=== TOP 10 STAR SHAPES (mule-like) ===")
    print(stars[['account_id', 'egonet_nodes', 'egonet_edges', 'expected_edges',
                 'shape_norm_score', 'in_deg', 'out_deg']].to_string(index=False))

cliques = result[result.ego_shape == 'NEAR_CLIQUE'].head(10)
if len(cliques):
    print("\n=== TOP 10 NEAR-CLIQUE SHAPES (fraud-cell-like) ===")
    print(cliques[['account_id', 'egonet_nodes', 'egonet_edges', 'expected_edges',
                   'shape_norm_score', 'in_deg', 'out_deg']].to_string(index=False))

result.to_csv(OUTPUT, index=False)
print(f"\nSaved to {OUTPUT}")

# ── validation against Phase 1 planted patterns ───────────────────────────────
# Ground truth from GROUND_TRUTH.csv (see project log Section 8.3 for full results).
known = {
    'A00013': 'mule collector',
    'A00014': 'mule forward target',
    'A00069': 'structuring',
    'A00070': 'structuring',
    'A00071': 'structuring',
    'A00055': 'scatter source',
}

print("\n=== DID ODDBALL INDEPENDENTLY FIND THE PLANTED PATTERNS? ===")
print("(ranked by shape-normalised score)\n")

for acct, label in known.items():
    row = result[result.account_id == acct]
    if len(row):
        rank = row.index[0] + 1
        pct  = 100 * rank / len(result)

        shape = row['ego_shape'].values[0]
        same_shape = result[result.ego_shape == shape].reset_index(drop=True)
        shape_rank = same_shape[same_shape.account_id == acct].index[0] + 1

        print(f"{acct} ({label}):")
        print(f"   overall rank {rank}/{len(result)} (top {pct:.1f}%)")
        print(f"   within {shape}s: rank {shape_rank}/{len(same_shape)}")
        print(f"   score={row['shape_norm_score'].values[0]:.2f}  "
              f"nodes={row['egonet_nodes'].values[0]}  "
              f"edges={row['egonet_edges'].values[0]}  "
              f"expected={row['expected_edges'].values[0]:.2f}\n")
    else:
        print(f"{acct} ({label}): not scored — egonet_edges = 0, "
              f"filtered out (neighbours don't transact with each other)\n")