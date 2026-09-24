"""
Module 5 — Phase 2b: Temporal Anomaly Detection
=================================================
Fills the gap OddBall (Phase 2) exposed: structuring and mule fan-in patterns
are invisible to egonet-shape analysis because their signature is *timing*,
not *topology*.

Method:
  For each account, find its single densest 48-hour transaction window.
  Within that window measure three signals:
    (a) regularity  — how regular the gaps between transactions are (low CV = suspicious)
    (b) burst_ratio — what fraction of the account's total activity fell in that window
    (c) uniformity  — how uniform the transaction amounts are (low CV = suspicious)
  Combine as a z-scored composite temporal_score.

Input:  ../data/inputs/temporal_data.csv   (exported from Aura)
Output: ../data/results/temporal_results.csv

Aura export Cypher (run once to refresh temporal_data.csv):
  MATCH (a:Account)-[t:TRANSACTED]->()
  WITH a.account_id AS account_id,
       count(t) AS tx_count,
       collect(toString(t.timestamp)) AS timestamps,
       collect(t.amount) AS amounts
  WHERE tx_count >= 5
  RETURN account_id, tx_count, timestamps, amounts

Infrastructure note (project log Section 6 + 8.2):
  Aura stores date/time fields as plain strings, not native Neo4j datetime types.
  The parse_list() helper below handles the "[item1, item2, ...]" list-as-string
  format that Aura CSV export produces (no quotes around individual items, so
  ast.literal_eval fails — split manually instead).

Known limitations (documented in project log Section 8.4):
  - burst_ratio over-dominates when accounts have high background tx volume:
    a launderer who blends ordinary activity currently scores *lower*, not higher.
    Fix outstanding: reweight so burst_tx_count and mean_gap_min count more.
  - A00013 (mule collector) and A00014 (mule target) still not scored —
    their signature is cross-account convergence, not single-account timing.
    Third independent confirmation (rule-based, OddBall, temporal) that mule
    fan-in needs a dedicated cross-account detector.
"""

from pathlib import Path
import pandas as pd
import numpy as np

# ── paths ─────────────────────────────────────────────────────────────────────
BASE   = Path(__file__).resolve().parent
INPUT  = BASE / "../data/inputs/temporal_data.csv"
OUTPUT = BASE / "../data/results/temporal_results.csv"


# ── parse Aura's list-as-string export format ─────────────────────────────────
def parse_list(x):
    """
    Aura exports list columns as "[item1, item2, item3]" with NO quotes
    around individual string items, so ast.literal_eval can't parse it
    (it reads dates as Python code and crashes).
    Strip the brackets and split manually instead.
    """
    if isinstance(x, list):
        return x
    x = x.strip()
    if x.startswith('[') and x.endswith(']'):
        x = x[1:-1]
    if not x:
        return []
    return [item.strip() for item in x.split(',')]


# ── load ──────────────────────────────────────────────────────────────────────
df = pd.read_csv(INPUT)
df['timestamps'] = df.timestamps.apply(parse_list)
df['amounts']    = df.amounts.apply(parse_list)

rows = []

for _, r in df.iterrows():
    times = pd.to_datetime(pd.Series(r.timestamps)).sort_values().reset_index(drop=True)
    amts  = np.array(r.amounts, dtype=float)

    if len(times) < 3:
        continue  # need enough points for a meaningful burst window

    # ── find the densest 48-hour window ──────────────────────────────────────
    # Instead of measuring regularity across the account's *entire* history
    # (which dilutes a short suspicious burst under years of normal background
    # activity), slide a 48-hour window and find the densest window.
    # Bug #1 fix: earlier version skipped this step; A00069's real hourly-burst
    # was drowned out by 7 scattered background transactions → rank 898/1174.
    # After windowing it surfaces correctly.
    best_count = 0
    best_idx   = (0, 0)
    for i in range(len(times)):
        window_end = times[i] + pd.Timedelta(hours=48)
        mask  = (times >= times[i]) & (times <= window_end)
        count = mask.sum()
        if count > best_count:
            best_count = count
            best_idx   = (i, i + count)

    if best_count < 3:
        continue  # no meaningful burst in this account at all

    burst_times = times[best_idx[0]:best_idx[1]].reset_index(drop=True)
    burst_amts  = amts[best_idx[0]:best_idx[1]]

    # ── signals within the burst window only ─────────────────────────────────
    gaps     = burst_times.diff().dropna().dt.total_seconds() / 60.0
    mean_gap = gaps.mean()
    cv_gap   = gaps.std() / mean_gap if mean_gap > 0 else np.nan

    burst_ratio = best_count / len(times)

    cv_amount = (burst_amts.std() / burst_amts.mean()
                 if burst_amts.mean() > 0 else np.nan)

    rows.append({
        'account_id':    r.account_id,
        'tx_count':      r.tx_count,
        'burst_tx_count': best_count,
        'mean_gap_min':  mean_gap,
        'cv_gap':        cv_gap,
        'burst_ratio':   burst_ratio,
        'cv_amount':     cv_amount,
        'mean_amount':   burst_amts.mean(),
    })

t = pd.DataFrame(rows)
print(f"Scored {len(t)} accounts with a detectable burst "
      f"(3+ total tx, 3+ in one 48h window)\n")


# ── composite temporal anomaly score ─────────────────────────────────────────
def z(s):
    """
    Z-score with a zero-variance guard.
    Bug #2 fix: cv_gap = 0.0 for all accounts in the planted structuring ring
    (perfectly regular intervals), so plain z-score divides by zero → NaN
    poisoned the entire composite. When std == 0 the feature carries no
    discriminating power, so contribute 0 instead of crashing.
    """
    std = s.std()
    if std == 0 or pd.isna(std):
        return pd.Series(0.0, index=s.index)
    return (s - s.mean()) / std


# Low CV (regularity/uniformity) = suspicious → negate so *higher* score = more suspicious
t['regularity_score']   = -z(t.cv_gap)
t['uniformity_score']   = -z(t.cv_amount)

# Short mean gap = more suspicious (scatter burst at 5-min gaps > structuring at 60-min gaps)
# Negate so that shorter gap → higher score
t['gap_speed_score']    = -z(t.mean_gap_min)

# burst_ratio penalises high-background accounts (e.g. A00069 has 17 total tx vs A00070's 13,
# so its ratio is lower despite identical planted burst). Fix (two parts):
#   1. z-score the *raw count* of burst transactions directly (burst_count_score) — volume-independent
#   2. Use a LOG-CAPPED ratio: log(1 + burst_tx) / log(1 + total_tx)
#      This compresses the penalty for small background volume differences.
#      A00069: log(11)/log(18) ≈ 0.888  vs  A00070: log(11)/log(14) ≈ 0.938 → nearly equal
t['burst_count_score']   =  z(t.burst_tx_count)
t['log_burst_ratio']     = (np.log1p(t.burst_tx_count) / np.log1p(t.tx_count))
t['burst_ratio_score']   =  z(t.log_burst_ratio)

# Weighted composite:
#   3× gap_speed_score    — shorter gaps are far more anomalous (5min >> 60min)
#   3× burst_count_score  — intrinsic burst intensity, volume-independent
#   2× regularity_score   — clock-like timing is a strong structuring signal
#   1× burst_ratio_score  — retains some signal but no longer dominates
#   1× uniformity_score   — equal-amount transactions
t['temporal_score'] = (3 * t.gap_speed_score
                       + 3 * t.burst_count_score
                       + 2 * t.regularity_score
                       + 1 * t.burst_ratio_score
                       + 1 * t.uniformity_score)

result = t.sort_values('temporal_score', ascending=False).reset_index(drop=True)


print("=== TOP 20 TEMPORAL ANOMALIES ===")
print(result[['account_id', 'tx_count', 'burst_tx_count', 'mean_gap_min',
              'cv_gap', 'burst_ratio', 'cv_amount',
              'temporal_score']].head(20).to_string(index=False))

result.to_csv(OUTPUT, index=False)
print(f"\nSaved to {OUTPUT}")


# ── validation against planted patterns ──────────────────────────────────────
# Full results and honest limitations documented in project log Section 8.4.
# Known issue: burst_ratio/total_tx weighting bias means A00069–74 span
# the entire rank range (2/7 → 7/7) despite identical burst signatures.
# Fix outstanding: reweight or cap total_tx influence before feeding composite score.
known = {
    'A00013': 'mule collector',
    'A00014': 'mule forward target',
    'A00069': 'structuring',
    'A00070': 'structuring',
    'A00071': 'structuring',
    'A00055': 'scatter source',
}

print("\n=== DID TEMPORAL SCORING FIND THE PLANTED PATTERNS? ===\n")
for acct, label in known.items():
    row = result[result.account_id == acct]
    if len(row):
        rank = row.index[0] + 1
        pct  = 100 * rank / len(result)
        print(f"{acct} ({label}): rank {rank}/{len(result)} (top {pct:.1f}%)")
        print(f"   score={row['temporal_score'].values[0]:.3f}  "
              f"total_tx={row['tx_count'].values[0]}  "
              f"burst_tx={row['burst_tx_count'].values[0]}  "
              f"mean_gap={row['mean_gap_min'].values[0]:.1f}min  "
              f"cv_gap={row['cv_gap'].values[0]:.3f}  "
              f"burst_ratio={row['burst_ratio'].values[0]:.2f}  "
              f"cv_amt={row['cv_amount'].values[0]:.3f}\n")
    else:
        print(f"{acct} ({label}): not scored "
              f"(fewer than 5 total tx, or no window with 5+ tx)\n")