"""Repeated and time-windowed typologies on observed transactions."""
from dataclasses import asdict
import numpy as np
from app.detect.common import Flows, HOUR, RuleMatch


def detect_rules(graph, config) -> list[dict]:
    import pandas as pd
    rows = sorted((d for *_, d in graph.edges(data=True)), key=lambda d: (d['t'], d['id']))
    if not rows:
        return []
    flows = Flows.build(pd.DataFrame(rows))
    matches: list[RuleMatch] = []
    links = []
    def add(rule, account, ids, detail):
        records = flows.tx[flows.tx.id.isin(ids)]
        accounts = sorted(set(records.src) | set(records.dst))
        matches.append(RuleMatch(rule, accounts, [account], list(map(str, ids)), detail))

    for aid, outgoing in flows.outbound.items():
        mask = (outgoing.amount >= config.structuring_min_inr) & (outgoing.amount <= config.structuring_max_inr)
        if mask.sum() >= config.structuring_count:
            add('Structuring', aid, outgoing.id[mask], {'transfers': int(mask.sum()),
                'reason': 'Repeated transfers in the configured structuring amount band.'})
        end_used = -1
        for i, t in enumerate(outgoing.t):
            if i <= end_used:
                continue
            end = int(np.searchsorted(outgoing.t, t + config.scatter_hours * HOUR, side='right'))
            count = len(set(outgoing.other[i:end]))
            if count >= config.scatter_receivers:
                add('Scatter', aid, outgoing.id[i:end], {'receivers': count,
                    'reason': f'Sent to {count} distinct recipients within {config.scatter_hours:g} hours.'})
                end_used = end - 1

    for aid, incoming in flows.inbound.items():
        outgoing = flows.outbound.get(aid)
        if outgoing is None:
            continue
        fan, rapid = [], []
        last_fan = last_rapid = -1
        # Non-overlapping incoming episodes prevent one receipt being counted repeatedly.
        for i, t in enumerate(incoming.t):
            if t > last_fan:
                end = int(np.searchsorted(incoming.t, t + config.fan_in_hours * HOUR, side='right'))
                received = incoming.amount[i:end].sum()
                lo = int(np.searchsorted(outgoing.t, incoming.t[end - 1], side='left'))
                hi = int(np.searchsorted(outgoing.t, t + config.fan_out_hours * HOUR, side='right'))
                # A small slice of a merchant's receipts must not claim a later rent
                # payment as forwarding. Require coverage of competing receipts in
                # the surrounding observed settlement window as well.
                context_lo = int(np.searchsorted(incoming.t, t - config.fan_out_hours * HOUR))
                context_hi = int(np.searchsorted(incoming.t, t + config.fan_out_hours * HOUR, side='right'))
                competing = incoming.amount[context_lo:context_hi].sum()
                if len(set(incoming.other[i:end])) >= config.fan_senders and outgoing.amount[lo:hi].sum() >= max(received, competing) * config.forward_share:
                    fan.append([*incoming.id[context_lo:context_hi], *outgoing.id[lo:hi]])
                    last_fan = t + config.fan_out_hours * HOUR
            if t > last_rapid:
                hi = int(np.searchsorted(outgoing.t, t + config.rapid_minutes * 60, side='right'))
                lo = int(np.searchsorted(outgoing.t, t, side='left'))
                if outgoing.amount[lo:hi].sum() >= incoming.amount[i] * config.forward_share:
                    rapid.append([incoming.id[i], *outgoing.id[lo:hi]])
                    last_rapid = t + config.rapid_minutes * 60
        # Count non-overlapping episodes, not receipt records (including context).
        if len(fan) >= config.fan_repeats:
            add('Mule fan-in', aid, sorted({tid for episode in fan for tid in episode}), {'occurrences': len(fan),
                'reason': f'Repeated fan-in with at least {config.forward_share:.0%} forwarded, across {len(fan)} separate windows; surrounding observed receipts are included to avoid attributing ordinary spending to a small receipt slice.'})
        if len(rapid) >= config.rapid_repeats:
            add('Rapid pass-through', aid, [x for episode in rapid for x in episode],
                {'occurrences': len(rapid), 'reason': f'Forwarded at least {config.forward_share:.0%} within {config.rapid_minutes:g} minutes on {len(rapid)} separate occasions.'})
        # Pool receipts in a short episode, then sum the matching outflows.
        i = 0
        while i < len(incoming.t):
            t = incoming.t[i]
            end = int(np.searchsorted(incoming.t, t + config.layer_hours * HOUR, side='left'))
            lo = int(np.searchsorted(outgoing.t, incoming.t[end - 1], side='left'))
            hi = int(np.searchsorted(outgoing.t, t + config.layer_hours * HOUR, side='left'))
            ratio = outgoing.amount[lo:hi].sum() / incoming.amount[i:end].sum()
            if config.layer_min_share <= ratio <= config.layer_max_share:
                links.append((aid, list(incoming.id[i:end]), list(outgoing.id[lo:hi])))
            i = end
    by_in = {}
    for link in links:
        for tid in link[1]:
            by_in.setdefault(tid, []).append(link)
    seen = set()
    for aid, ins, outs in links:
        for tid in outs:
            for next_aid, next_ins, next_outs in by_in.get(tid, []):
                if aid == next_aid or (aid, next_aid, tid) in seen:
                    continue
                seen.add((aid, next_aid, tid))
                ids = sorted(set(ins + outs + next_ins + next_outs))
                records = flows.tx[flows.tx.id.isin(ids)]
                accounts = sorted(set(records.src) | set(records.dst))
                if len(accounts) >= 4:
                    matches.append(RuleMatch('Layering chain', accounts, [aid, next_aid], ids,
                        {'reason': f'At least three hops with intermediaries forwarding {config.layer_min_share:.0%}–{config.layer_max_share:.0%} of pooled receipts in under {config.layer_hours:g} hours.'}))
    return [asdict(m) for m in matches]
