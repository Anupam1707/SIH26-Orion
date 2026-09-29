"""Fund blocking service: bridges the trace, prediction, and min-cut modules.

Provides high-level functions called by the API router.
"""

from __future__ import annotations

from datetime import datetime

from app.block.mincut import FreezeRecommendation, recommend, simulate_freeze
from app.data import Public
from app.graph.trace import trace_case


def get_recommendations(
    public: Public,
    graph,
    complaint: dict,
    risks: dict,
    demo_clock: datetime,
    config,
    max_accounts: int = 3,
) -> dict:
    """Build freeze recommendations for a complaint at the current demo clock."""
    trace = trace_case(graph, complaint, risks,
                       config.trace_max_hops, config.trace_min_share)

    # Sum withdrawals already made by each account as of the demo clock.
    wd = public.withdrawals_upto(demo_clock)
    chain_ids = {n["id"] for n in trace["nodes"]}
    chain_wd = wd[wd.account_id.isin(chain_ids)]
    withdrawals_by_account: dict[str, float] = {}
    for row in chain_wd.groupby("account_id").amount_inr.sum().items():
        withdrawals_by_account[row[0]] = float(row[1])

    case_amount = float(complaint["amount_inr"])
    rec = recommend(trace, withdrawals_by_account, case_amount, max_accounts)

    # Enrich with account details.
    accounts_df = public.accounts
    account_details = []
    for aid in rec.accounts:
        found = accounts_df[accounts_df.id == aid]
        detail = {"id": aid, "reason": rec.reasons.get(aid, "")}
        if not found.empty:
            row = found.iloc[0]
            detail["bank"] = row.bank
            detail["home_district_id"] = row.home_district_id
        # Find the node's inferred role and hop from the trace.
        for node in trace["nodes"]:
            if node["id"] == aid:
                detail["inferred_role"] = node["inferred_role"]
                detail["hop"] = node["hop"]
                detail["risk"] = node["risk"]
                break
        account_details.append(detail)

    return {
        "complaint_id": complaint["id"],
        "demo_clock": demo_clock.isoformat(),
        "recommended_accounts": account_details,
        "money_reachable_before_inr": rec.money_reachable_before,
        "money_reachable_after_inr": rec.money_reachable_after,
        "prevented_inr": rec.prevented_inr,
        "prevented_pct": rec.prevented_pct,
        "trace_node_count": len(trace["nodes"]),
        "trace_edge_count": len(trace["edges"]),
        "max_accounts": max_accounts,
    }


def run_simulation(
    public: Public,
    graph,
    complaint: dict,
    risks: dict,
    config,
    accounts_to_freeze: list[str],
) -> dict:
    """Simulate freezing specific accounts and return before/after metrics."""
    trace = trace_case(graph, complaint, risks,
                       config.trace_max_hops, config.trace_min_share)
    return simulate_freeze(trace, accounts_to_freeze)
