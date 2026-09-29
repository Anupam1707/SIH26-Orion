"""Shared structures for the detectors."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

HOUR = 3600
MINUTE = 60


@dataclass
class RuleMatch:
    """One occurrence of a typology rule, with the transactions that triggered it (spec §8.2)."""

    rule: str
    accounts: list[str]  # every account involved
    flagged: list[str]  # the accounts the rule is *about* (they receive the hit)
    tx_ids: list[str]
    detail: dict = field(default_factory=dict)


@dataclass
class Side:
    """One direction of an account's transactions, sorted by time."""

    t: np.ndarray  # epoch seconds
    amount: np.ndarray  # rupees
    other: np.ndarray  # counterparty account id
    id: np.ndarray  # transaction id
    row: np.ndarray  # global row index (time order), used to break ties


@dataclass
class Flows:
    """Per-account inbound / outbound transaction arrays, built once per detection run."""

    tx: pd.DataFrame
    inbound: dict[str, Side]
    outbound: dict[str, Side]

    @classmethod
    def build(cls, tx: pd.DataFrame) -> "Flows":
        tx = tx.reset_index(drop=True)
        cols = {
            "t": tx["t"].to_numpy(),
            "amount": tx["amount_inr"].to_numpy(),
            "id": tx["id"].to_numpy(),
            "row": np.arange(len(tx)),
        }
        src = tx["src"].to_numpy()
        dst = tx["dst"].to_numpy()

        def group(key: np.ndarray, other: np.ndarray) -> dict[str, Side]:
            order = np.argsort(key, kind="stable")  # stable: keeps time order inside each account
            key_sorted = key[order]
            bounds = np.flatnonzero(key_sorted[1:] != key_sorted[:-1]) + 1
            starts = np.concatenate([[0], bounds])
            ends = np.concatenate([bounds, [len(order)]])
            out: dict[str, Side] = {}
            for s, e in zip(starts, ends):
                idx = order[s:e]
                out[str(key_sorted[s])] = Side(
                    t=cols["t"][idx], amount=cols["amount"][idx], other=other[idx], id=cols["id"][idx], row=cols["row"][idx]
                )
            return out

        if len(tx) == 0:
            return cls(tx=tx, inbound={}, outbound={})
        return cls(tx=tx, inbound=group(dst, src), outbound=group(src, dst))
