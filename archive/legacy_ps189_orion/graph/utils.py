"""
graph/utils.py

Shared helpers:
  - clean_record()    : converts NaN / NaT to None so Cypher doesn't get 'nan'
  - batch_merge()     : chunks a list of records into UNWIND batches
  - load_csv()        : reads a CSV with safe type handling
  - run_batches()     : drives batch_merge with a tqdm progress bar
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Callable, Iterable

import pandas as pd
from loguru import logger
from tqdm import tqdm


# ── Record cleaning ───────────────────────────────────────────────────────────

def clean_record(record: dict) -> dict:
    """Replace float NaN / pandas NaT / 'nan' strings with None."""
    cleaned = {}
    for k, v in record.items():
        if v is None:
            cleaned[k] = None
        elif isinstance(v, float) and math.isnan(v):
            cleaned[k] = None
        elif str(v) in {"NaT", "nan", "None"}:
            cleaned[k] = None
        else:
            cleaned[k] = v
    return cleaned


# ── CSV loading ───────────────────────────────────────────────────────────────

def load_csv(path: Path, low_memory: bool = False) -> pd.DataFrame:
    """Read a CSV file; return empty DataFrame on missing file."""
    if not path.exists():
        logger.warning(f"CSV not found, skipping: {path}")
        return pd.DataFrame()
    df = pd.read_csv(path, low_memory=low_memory)
    logger.info(f"Loaded {len(df):,} rows from {path.name}")
    return df


# ── Batched UNWIND loading ────────────────────────────────────────────────────

def batch_merge(
    session,
    records: list[dict],
    cypher: str,
    batch_size: int = 500,
    desc: str = "",
) -> int:
    """
    Execute `cypher` in batches using UNWIND over `records`.
    The Cypher query must reference `$batch` as the list parameter.

    Returns total rows written.
    """
    total = 0
    batches = [records[i : i + batch_size] for i in range(0, len(records), batch_size)]
    for chunk in tqdm(batches, desc=desc or "Loading", unit="batch", leave=False):
        session.run(cypher, batch=chunk)
        total += len(chunk)
    return total


def run_batches(
    driver,
    df: pd.DataFrame,
    cypher: str,
    desc: str,
    batch_size: int = 500,
    transform: Callable[[dict], dict] | None = None,
) -> int:
    """
    Convert a DataFrame to cleaned records, apply optional transform, then
    load in batches via batch_merge.
    """
    if df.empty:
        logger.warning(f"[{desc}] Empty DataFrame — skipping.")
        return 0

    records: list[dict] = []
    for row in df.to_dict(orient="records"):
        r = clean_record(row)
        if transform:
            r = transform(r)
        records.append(r)

    with driver.session() as session:
        written = batch_merge(session, records, cypher, batch_size=batch_size, desc=desc)

    logger.success(f"[{desc}] {written:,} rows written.")
    return written
