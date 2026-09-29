"""Leakage, time split, probability, explanation and evaluation regression checks."""
import copy
from datetime import datetime, timedelta

import numpy as np

from app.data import Public
from app.predict import baseline, kde, xgb
from app.predict.cases import make_cases, time_split, WINDOWS
from app.predict.evaluate import metrics, evaluate
from app.predict.features import extract, FEATURE_NAMES


def test_case_schedule_split_and_labels(world, scenario):
    cases = make_cases(world)
    train, test = time_split(cases, scenario.start)
    assert len(cases) == len(world.frauds)
    assert all(c.prediction_time < scenario.start + timedelta(days=70) for c in train)
    assert all(scenario.start + timedelta(days=70) <= c.prediction_time < scenario.start + timedelta(days=90) for c in test)
    assert not any(c.is_demo for c in train + test)
    for case in cases:
        assert np.all(case.labels[2] <= case.labels[6])
        assert np.all(case.labels[6] <= case.labels[24])
        assert case.labels[24].sum() > 0


def test_no_future_or_hidden_fields_enter_features(world, scenario):
    case = make_cases(world)[-1]
    public = Public.from_world(world)
    first = extract(public, case.complaint_id, case.prediction_time, scenario.detection)
    changed = copy.deepcopy(world)
    changed.transactions.loc[changed.transactions.ts > case.prediction_time, 'amount_inr'] = 10**9
    changed.withdrawals.loc[changed.withdrawals.ts > case.prediction_time, ['amount_inr', 'atm_id']] = [10**9, 'ATM001']
    changed.accounts['role_truth'] = 'changed'
    changed.transactions['fraud_id'] = 'changed'
    changed.withdrawals['network_id'] = 'changed'
    second = extract(Public.from_world(changed), case.complaint_id, case.prediction_time, scenario.detection)
    np.testing.assert_array_equal(first.base, second.base)
    np.testing.assert_array_equal(first.history_xy, second.history_xy)
    np.testing.assert_array_equal(kde.density(first, 1.), kde.density(second, 1.))
    np.testing.assert_array_equal(baseline.spatial_scores(first), baseline.spatial_scores(second))
    assert first.evidence == second.evidence
    assert datetime.fromisoformat(first.max_input_ts) <= case.prediction_time
    own_ids = set(world.withdrawals[world.withdrawals.fraud_id == world.meta['demo_fraud_id']].id)
    assert not own_ids.intersection(first.history.id)
    assert all(datetime.fromisoformat(r['ts']) <= case.prediction_time
               for group in ('transactions', 'withdrawals') for r in first.evidence[group])


def test_bootstrap_denominator_ceiling_and_empty_windows():
    actual = [{'a'}, set(), {'b', 'c'}]
    ranked = [['a','x','y','z','q'], ['a','x','y','z','q'], ['b','c','x','y','z']]
    result = metrics(actual, ranked, 42)
    assert result['n'] == 3
    assert result['hit_rate'] == 2 / 3
    assert np.isclose(result['precision_at_5'], .2)
    assert np.isclose(result['precision_ceiling'], .2)
    assert result == metrics(actual, ranked, 42)
    assert result['hit_rate_ci95'][0] <= result['hit_rate'] <= result['hit_rate_ci95'][1]
    assert metrics([], [], 42)['hit_rate'] is None


def test_xgboost_contributions_sum_to_log_odds_and_repeat():
    rng = np.random.default_rng(7)
    matrix = rng.normal(size=(100, len(FEATURE_NAMES)))
    labels = (matrix[:, 0] > 0).astype(float)
    model = xgb.fit(matrix, labels, 42)
    probabilities, contributions = xgb.predict(model, matrix)
    np.testing.assert_allclose(1 / (1 + np.exp(-contributions.sum(axis=1))), probabilities, rtol=1e-5)
    repeated, _ = xgb.predict(xgb.fit(matrix, labels, 42), matrix)
    np.testing.assert_array_equal(probabilities, repeated)
    assert xgb.fit(matrix, np.zeros(len(matrix)), 42) is None


def test_probability_no_history_fallback(world, scenario):
    case = make_cases(world)[0]
    features = extract(Public.from_world(world), case.complaint_id, case.prediction_time, scenario.detection)
    features.history = features.history.iloc[:0]
    features.history_xy = np.empty((0, 2))
    features.last_age_days[:] = np.inf
    assert np.all(kde.density(features, 1.) == 0)
    probs = baseline.probabilities(baseline.spatial_scores(features), 1.)
    assert np.all(probs == probs[0])
    assert np.all((probs >= 0) & (probs <= 1))


def test_api_models_sources_clocks_and_training(client, world, scenario):
    client.post('/demo/reset')
    cid = world.meta['demo_complaint_id']
    assert client.get(f'/predictions/{cid}').status_code == 404
    initial_report = client.get('/evaluation').json()
    started = client.post('/demo/start').json()
    try:
        assert len(client.get('/atms').json()) == len(world.atms)
        for model in ('baseline', 'kde', 'xgboost'):
            for hours in WINDOWS:
                res = client.get(f'/predictions/{cid}?model={model}&window={hours}')
                assert res.status_code == 200
                data = res.json()
                assert data['prediction_time'] <= started['demo_clock']
                assert data['max_input_ts'] <= data['prediction_time']
                assert data['training']['latest_outcome_at'] <= data['training']['available_at'] <= data['prediction_time']
                assert len(data['atms']) == len(world.atms)
                probabilities = [a['probability'] for a in data['atms']]
                assert probabilities == sorted(probabilities, reverse=True)
                assert all(0 <= p <= 1 for p in probabilities)
                assert all(len(a['reasons']) == 3 for a in data['atms'])
                assert all('network' not in r['text'].lower() for a in data['atms'] for r in a['reasons'])
                assert not any(hidden in res.text for hidden in ('role_truth', 'fraud_id', 'network_id'))
        assert client.get(f'/predictions/{cid}?model=invalid').status_code == 422
        assert client.get(f'/predictions/{cid}?window=12').status_code == 422
        report = client.get('/evaluation').json()
        assert len(report['rows']) == 4 * 3 * 3
        assert all('n' in r and 'hit_rate_ci95' in r and 'precision_ceiling' in r for r in report['rows'])
        assert all({r['model'] for r in report['rows'] if r['strategy'] == strategy} == {'baseline','kde','xgboost'}
                   for strategy in {r['strategy'] for r in report['rows']})
        assert report['test_cases_available'] >= initial_report['test_cases_available']
    finally:
        client.post('/demo/reset')


def test_historical_forecasts_never_train_on_their_future(client, world, scenario):
    artifact = client.app.state.demo.predictions
    cases = {c.complaint_id: c for c in make_cases(world)}
    cutoff = scenario.start + timedelta(days=70)
    for cid, prediction in artifact['cases'].items():
        for tid in prediction['training']['case_ids']:
            assert cases[tid].prediction_time < cutoff
            assert cases[tid].outcome_end <= min(cases[cid].prediction_time, cutoff)
            assert tid != cid
    # Full CLI evaluation includes every time-split test case, not just cases with a positive label.
    _, test = time_split(list(cases.values()), scenario.start)
    assert artifact['full_evaluation']['test_cases_total'] == len(test)
    report = evaluate(test, artifact['cases'], sorted(world.atms.id), scenario.seed, scenario.start)
    assert report['test_cases_available'] == 0
