from datetime import datetime, timedelta
import json
import networkx as nx
import numpy as np
import pytest
from app.data import Public
from app.detect.service import analyze
from app.detect.temporal import temporal, zscore
from app.detect.oddball import oddball
from app.graph.builder import build_graph
from app.graph.trace import trace_case


@pytest.fixture(scope='module')
def observed(world, scenario):
    public = Public.from_world(world)
    demo = world.frauds[world.frauds.is_demo].iloc[0]
    tx = world.transactions[world.transactions.fraud_id == demo.id]
    complaint = world.complaints[world.complaints.id == demo.complaint_id].iloc[0].to_dict()
    clock = max(tx.ts.max(), complaint['reported_at']).to_pydatetime()
    snapshot = analyze(public, clock, scenario.detection)
    return public, clock, snapshot, tx, complaint


def test_rules_expected_accounts_and_merchant_negative(observed, world):
    _, _, snapshot, _, _ = observed
    flagged = lambda rule: {a for m in snapshot['matches'] if m['rule'] == rule for a in m['flagged']}
    accounts = world.accounts.set_index('id')
    collectors = set(accounts[accounts.role_truth == 'collector'].index)
    assert collectors <= flagged('Mule fan-in')
    assert not set(accounts[accounts.role_truth == 'merchant'].index) & flagged('Mule fan-in')
    for network, rule, role in [('N_B', 'Structuring', 'mule_l1'), ('N_C', 'Scatter', 'collector')]:
        frauds = set(world.frauds[world.frauds.network_id == network].id)
        tx = world.transactions[world.transactions.fraud_id.isin(frauds)]
        expected = set(tx.src) & set(accounts[accounts.role_truth == role].index)
        assert expected <= flagged(rule)
    assert set(accounts[accounts.role_truth == 'mule_l1'].index) <= flagged('Rapid pass-through')


def test_demo_exact_trace_and_patterns(observed, scenario):
    public, clock, snapshot, demo_tx, complaint = observed
    trace = trace_case(build_graph(public, clock), complaint, snapshot['risks'])
    assert {e['id'] for e in trace['edges']} == set(demo_tx.id)
    assert len(trace['nodes']) == 1 + scenario.demo_case.path.l1_mules + 1 + scenario.demo_case.path.l2_accounts
    assert trace['hop_order'] == [1, 2, 3]
    collector = next(n for n in trace['nodes'] if n['inferred_role'] == 'collector')
    assert {'Mule fan-in', 'Layering chain'} <= set(collector['rules'])
    assert all(0 <= n['risk'] <= 1 for n in trace['nodes'])


def test_future_records_and_hidden_truth_cannot_change_analysis(world, scenario, observed):
    public, clock, snapshot, _, _ = observed
    import copy
    altered = copy.deepcopy(world)
    altered.transactions.loc[altered.transactions.ts > clock, 'amount_inr'] = 999999999
    altered.accounts['role_truth'] = 'collector'
    altered.transactions['fraud_id'] = 'bogus'
    altered.withdrawals['network_id'] = 'bogus'
    assert analyze(Public.from_world(altered), clock, scenario.detection) == snapshot
    encoded = json.dumps(snapshot)
    assert all(field not in encoded for field in ('role_truth', 'fraud_id', 'network_id'))
    known = set(public.tx_upto(clock).id)
    assert all(set(m['tx_ids']) <= known for m in snapshot['matches'])


def test_trace_respects_chronology_pruning_and_conservation():
    now = datetime.fromisoformat('2026-08-30T10:15:00+05:30')
    graph = nx.MultiDiGraph()
    for tid, src, dst, amount, minutes in [('early','a','b',100,0), ('receipt','v','a',100,1),
        ('tiny','a','x',4,2), ('forward','a','b',90,3), ('double','a','c',90,4)]:
        graph.add_edge(src,dst,key=tid,id=tid,src=src,dst=dst,amount_inr=amount,ts=now+timedelta(minutes=minutes))
    result = trace_case(graph, {'victim_account_id':'v','amount_inr':100,'incident_at':now})
    assert {e['id'] for e in result['edges']} == {'receipt','forward','double'}
    assert sum(e['traced_amount_inr'] for e in result['edges'] if e['src']=='a') <= 100


def test_temporal_constant_guard_and_densest_window():
    assert np.array_equal(zscore([0,0,0]), [0,0,0])
    graph = nx.MultiDiGraph()
    for aid in ['a','b']:
        for i, t in enumerate([0,1000000,1000060,1000120,1000180,1000240]):
            graph.add_edge(aid,'sink',id=f'{aid}{i}',t=t,amount_inr=100)
    scores = temporal(graph)
    assert scores['a']['temporal_tx_ids'] == ['a1','a2','a3','a4','a5']
    assert scores['a']['temporal_score'] == 0
    assert scores['sink']['temporal_score'] == 0
    assert all(np.isfinite(v['oddball_z']) for v in oddball(graph).values())
