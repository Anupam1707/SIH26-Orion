"""Node-capacity min-cut for fund blocking (spec §10).

Given a traced case subgraph, recommend the fewest accounts to freeze to stop the
most money from reaching cash-out.  The algorithm:

1. Build a flow graph from the traced case edges.
2. Add super-source S → victim (infinite capacity) and terminal accounts → super-sink T.
3. Split each intermediate node v into v_in → v_out with capacity that favours
   cutting fewer accounts first, then the ones carrying more money.
4. Run NetworkX minimum_cut.
5. Greedy fallback when the cut has more than k accounts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import networkx as nx

INF = float("inf")


@dataclass(frozen=True)
class FreezeRecommendation:
    """The set of accounts to freeze plus before/after flow metrics."""

    accounts: list[str]
    reasons: dict[str, str]  # account_id → why it was chosen
    money_reachable_before: float
    money_reachable_after: float
    prevented_inr: float
    prevented_pct: float


def _build_flow_graph(
    trace: dict,
    withdrawals_by_account: dict[str, float],
    case_amount: float,
) -> tuple[nx.DiGraph, set[str]]:
    """Build the node-split flow graph from a case trace.

    Returns (flow_graph, terminal_account_ids).
    """
    victim = trace["complaint"]["victim_account_id"]

    # Determine which accounts are terminals (L2 / recipients at max hop).
    max_hop = max((n["hop"] for n in trace["nodes"]), default=0)
    terminals: set[str] = set()
    for node in trace["nodes"]:
        if node["id"] == victim:
            continue
        # Accounts at max hop or those with withdrawals are terminals.
        if node["hop"] == max_hop or node["id"] in withdrawals_by_account:
            terminals.add(node["id"])

    # Money that flowed through each account (sum of traced incoming edges).
    money_through: dict[str, float] = {}
    for edge in trace["edges"]:
        dst = edge["dst"]
        money_through[dst] = money_through.get(dst, 0) + edge["traced_amount_inr"]
    # Victim has the full amount.
    money_through[victim] = case_amount

    G = nx.DiGraph()
    S, T = "__S__", "__T__"
    G.add_edge(S, victim, capacity=INF)

    # Node splitting for every account except victim, S, T.
    node_ids = {n["id"] for n in trace["nodes"]}
    for aid in node_ids:
        if aid == victim:
            continue
        if aid in terminals:
            # Terminal → T with infinite capacity (we want to cut upstream).
            G.add_node(f"{aid}_in")
            G.add_node(f"{aid}_out")
            flow = money_through.get(aid, 0)
            already_withdrawn = withdrawals_by_account.get(aid, 0)
            remaining = max(flow - already_withdrawn, 0)
            if remaining < 1:
                # Money already fully withdrawn — freezing stops nothing.
                cap = INF
            else:
                cap = 1 - 0.01 * (flow / case_amount) if case_amount > 0 else 1
            G.add_edge(f"{aid}_in", f"{aid}_out", capacity=cap)
            G.add_edge(f"{aid}_out", T, capacity=INF)
        else:
            # Intermediate node.
            G.add_node(f"{aid}_in")
            G.add_node(f"{aid}_out")
            flow = money_through.get(aid, 0)
            already_withdrawn = withdrawals_by_account.get(aid, 0)
            remaining = max(flow - already_withdrawn, 0)
            if remaining < 1:
                cap = INF
            else:
                cap = 1 - 0.01 * (flow / case_amount) if case_amount > 0 else 1
            G.add_edge(f"{aid}_in", f"{aid}_out", capacity=cap)

    # Edges: u_out → v_in with infinite capacity.
    for edge in trace["edges"]:
        src, dst = edge["src"], edge["dst"]
        src_node = src if src == victim else f"{src}_out"
        dst_node = f"{dst}_in"
        if G.has_node(src_node) and G.has_node(dst_node):
            # Use edge key to handle parallel edges.
            if not G.has_edge(src_node, dst_node):
                G.add_edge(src_node, dst_node, capacity=INF)

    return G, terminals


def _cut_accounts(G: nx.DiGraph) -> list[str]:
    """Run min-cut and extract the account IDs from cut v_in→v_out edges."""
    S, T = "__S__", "__T__"
    if not G.has_node(S) or not G.has_node(T):
        return []
    try:
        _, (reachable, _) = nx.minimum_cut(G, S, T)
    except nx.NetworkXError:
        return []

    accounts: list[str] = []
    for u in reachable:
        if isinstance(u, str) and u.endswith("_in"):
            aid = u[:-3]
            out_node = f"{aid}_out"
            if out_node not in reachable:
                accounts.append(aid)
    return sorted(accounts)


def _money_flow(
    G: nx.DiGraph,
    frozen: set[str] | None = None,
) -> float:
    """Compute max flow from S to T, optionally with some accounts frozen."""
    S, T = "__S__", "__T__"
    if not G.has_node(S) or not G.has_node(T):
        return 0.0
    if frozen:
        G = G.copy()
        for aid in frozen:
            in_node, out_node = f"{aid}_in", f"{aid}_out"
            if G.has_edge(in_node, out_node):
                G.remove_edge(in_node, out_node)
    try:
        return float(nx.maximum_flow_value(G, S, T))
    except nx.NetworkXError:
        return 0.0


def _build_amount_graph(trace: dict, victim: str) -> nx.DiGraph:
    """Build a flow graph with edge capacities = transaction amounts for simulation."""
    G = nx.DiGraph()
    S, T = "__S__", "__T__"

    max_hop = max((n["hop"] for n in trace["nodes"]), default=0)
    terminals = set()
    for n in trace["nodes"]:
        if n["id"] != victim and n["hop"] == max_hop:
            terminals.add(n["id"])

    node_ids = {n["id"] for n in trace["nodes"]}
    G.add_edge(S, victim, capacity=INF)
    for aid in node_ids:
        if aid == victim:
            continue
        G.add_node(f"{aid}_in")
        G.add_node(f"{aid}_out")
        G.add_edge(f"{aid}_in", f"{aid}_out", capacity=INF)
        if aid in terminals:
            G.add_edge(f"{aid}_out", T, capacity=INF)

    # Use summed transaction amounts as edge capacities.
    edge_caps: dict[tuple[str, str], float] = {}
    for edge in trace["edges"]:
        src = edge["src"] if edge["src"] == victim else f"{edge['src']}_out"
        dst = f"{edge['dst']}_in"
        key = (src, dst)
        edge_caps[key] = edge_caps.get(key, 0) + edge["traced_amount_inr"]
    for (src, dst), cap in edge_caps.items():
        if G.has_node(src) and G.has_node(dst):
            G.add_edge(src, dst, capacity=cap)
    return G


def _greedy_select(
    G: nx.DiGraph,
    candidates: list[str],
    k: int,
) -> list[str]:
    """Greedy fallback: pick the account whose removal reduces flow the most, up to k."""
    selected: list[str] = []
    remaining = set(candidates)
    for _ in range(min(k, len(candidates))):
        best_aid, best_drop = None, -1.0
        base_flow = _money_flow(G, set(selected))
        for aid in remaining:
            new_flow = _money_flow(G, set(selected) | {aid})
            drop = base_flow - new_flow
            if drop > best_drop:
                best_drop = drop
                best_aid = aid
        if best_aid is None or best_drop <= 0:
            break
        selected.append(best_aid)
        remaining.discard(best_aid)
    return selected


def recommend(
    trace: dict,
    withdrawals_by_account: dict[str, float],
    case_amount: float,
    max_accounts: int = 3,
) -> FreezeRecommendation:
    """Recommend accounts to freeze for a traced case.

    Args:
        trace: Output of trace_case.
        withdrawals_by_account: Sum of withdrawals already made per account at the demo clock.
        case_amount: The complaint's total amount.
        max_accounts: Maximum accounts in the recommendation (k).
    """
    G, terminals = _build_flow_graph(trace, withdrawals_by_account, case_amount)
    cut = _cut_accounts(G)

    if len(cut) > max_accounts:
        # Greedy fallback: use all intermediate + terminal accounts as candidates.
        all_accounts = [n["id"] for n in trace["nodes"]
                        if n["id"] != trace["complaint"]["victim_account_id"]]
        cut = _greedy_select(G, all_accounts, max_accounts)

    # Build reasons.
    money_through: dict[str, float] = {}
    for edge in trace["edges"]:
        money_through[edge["dst"]] = money_through.get(edge["dst"], 0) + edge["traced_amount_inr"]

    reasons: dict[str, str] = {}
    for aid in cut:
        role = "unknown"
        for n in trace["nodes"]:
            if n["id"] == aid:
                role = n["inferred_role"]
                break
        flow = money_through.get(aid, 0)
        already = withdrawals_by_account.get(aid, 0)
        if already > 0:
            reasons[aid] = (
                f"Inferred role: {role}. ₹{int(flow):,} flowed through; "
                f"₹{int(already):,} already withdrawn. Freezing prevents remaining funds from reaching cash-out."
            )
        else:
            reasons[aid] = (
                f"Inferred role: {role}. ₹{int(flow):,} traced through this account. "
                f"Freezing this chokepoint prevents funds from reaching cash-out."
            )

    # Simulate before/after.
    amount_G = _build_amount_graph(trace, trace["complaint"]["victim_account_id"])
    before = _money_flow(amount_G)
    after = _money_flow(amount_G, set(cut))
    prevented = max(before - after, 0)
    pct = prevented / before if before > 0 else 0.0

    return FreezeRecommendation(
        accounts=cut,
        reasons=reasons,
        money_reachable_before=before,
        money_reachable_after=after,
        prevented_inr=prevented,
        prevented_pct=pct,
    )


def simulate_freeze(
    trace: dict,
    accounts_to_freeze: list[str],
) -> dict:
    """Simulate freezing specific accounts: return before/after money reachable."""
    victim = trace["complaint"]["victim_account_id"]
    amount_G = _build_amount_graph(trace, victim)
    before = _money_flow(amount_G)
    after = _money_flow(amount_G, set(accounts_to_freeze))
    prevented = max(before - after, 0)
    return {
        "accounts_frozen": accounts_to_freeze,
        "money_reachable_before_inr": before,
        "money_reachable_after_inr": after,
        "prevented_inr": prevented,
        "prevented_pct": prevented / before if before > 0 else 0.0,
    }
