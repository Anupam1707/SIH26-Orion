from time import perf_counter


def test_preview_evidence_clock_and_reset(client):
    summary = client.get('/summary').json()
    initial = client.get('/complaints').json()
    assert summary['complaints'] == len(initial)
    started = client.post('/demo/start').json()
    cid = started['complaint_id']
    assert cid not in {c['id'] for c in initial}
    t0 = perf_counter()
    response = client.get(f'/cases/{cid}/trace')
    assert perf_counter() - t0 < 2
    assert response.status_code == 200
    trace = response.json()
    assert len(trace['nodes']) == 7
    assert len(trace['edges']) == 8
    for node in trace['nodes']:
        detail = client.get('/accounts/' + node['id']).json()
        assert 'role_truth' not in detail
        assert all(t['ts'] <= started['demo_clock'] for t in detail['source_transactions'])
        assert {i for s in detail['signals'] for i in s['tx_ids']} <= {t['id'] for t in detail['source_transactions']}
    client.post('/demo/reset')
    assert client.get('/summary').json() == summary
    assert client.get(f'/cases/{cid}/trace').status_code == 404
    assert client.get('/accounts/missing').status_code == 404
