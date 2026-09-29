"""Precompute rolling-origin predictions and a frozen day-70 held-out evaluation."""
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

from app.data import Public
from app.predict import baseline, kde, xgb
from app.predict.cases import make_cases, time_split, MODELS, WINDOWS
from app.predict.evaluate import evaluate
from app.predict.explain import explanations
from app.predict.features import extract, FEATURE_NAMES
from app.sim.model import World
from app.sim.scenario import Scenario


def build_predictions(world: World, scenario: Scenario, output: Path | None = None) -> dict:
    public = Public.from_world(world)
    cases = make_cases(world)
    train, test = time_split(cases, scenario.start)
    cutoff = scenario.start + timedelta(days=70)
    features = {}
    for index, case in enumerate(cases):
        features[case.complaint_id] = extract(public, case.complaint_id, case.prediction_time, scenario.detection)
        if (index + 1) % 20 == 0:
            print(f'  prediction features: {index + 1}/{len(cases)}', flush=True)
    densities = {(cid, bw): kde.density(f, bw) for cid, f in features.items() for bw in kde.BANDWIDTHS_KM}
    labels24 = {c.complaint_id: c.labels[24] for c in cases}
    predictions, fits, bundles = {}, {}, {}
    for case in cases:
        f = features[case.complaint_id]
        # Freeze at day 70 for the test set. Earlier forecasts get expanding-history fits.
        available_at = min(case.prediction_time, cutoff)
        prior = [c for c in train if c.outcome_end <= available_at and c.prediction_time < case.prediction_time]
        key = tuple(c.complaint_id for c in prior)
        if key not in fits:
            bandwidth = kde.choose_bandwidth(list(key), features, densities, labels24)
            models = {}
            matrix = np.concatenate([features[cid].matrix(densities[cid, bandwidth]) for cid in key]) if key else np.empty((0, len(FEATURE_NAMES)))
            for hours in WINDOWS:
                labels = np.concatenate([c.labels[hours] for c in prior]) if prior else np.array([])
                models[hours] = xgb.fit(matrix, labels, scenario.seed)
            fits[key] = (bandwidth, models)
        bandwidth, models = fits[key]
        density = densities[case.complaint_id, bandwidth]
        matrix = f.matrix(density)
        meta = {'n': len(prior), 'case_ids': list(key), 'bandwidth_km': bandwidth,
                'available_at': available_at.isoformat(),
                'latest_outcome_at': max((c.outcome_end for c in prior), default=None),
                'method': 'Expanding-history training before day 71; frozen day-70 fit for held-out cases.'}
        if meta['latest_outcome_at']:
            meta['latest_outcome_at'] = meta['latest_outcome_at'].isoformat()
        payload = {'complaint_id': case.complaint_id, 'prediction_time': f.clock.isoformat(),
                   'max_input_ts': f.max_input_ts, 'chain_accounts': f.chain_ids, 'linked_accounts': f.linked_ids,
                   'holder_accounts': f.holder_ids, 'training': meta, 'evidence': f.evidence, 'models': {}}
        for model_name in MODELS:
            payload['models'][model_name] = {}
            for hours in WINDOWS:
                expected = float(np.mean([c.labels[hours].sum() for c in prior])) if prior else hours / 24
                fallback = None
                contributions = None
                scores = baseline.spatial_scores(f)
                if model_name == 'kde':
                    if not len(f.history):
                        fallback = 'No past chain-linked withdrawals: KDE falls back to the recency baseline (uniform spatial prior).'
                    elif density.sum() > 0:
                        scores = density
                    else:
                        fallback = 'KDE density is numerically zero: using the recency baseline.'
                probabilities = baseline.probabilities(scores, expected)
                if model_name == 'xgboost':
                    if models[hours] is None:
                        fallback = 'Earlier completed training cases do not contain both outcome classes; XGBoost falls back to the recency baseline.'
                    else:
                        probabilities, contributions = xgb.predict(models[hours], matrix)
                rows = []
                for i, atm in enumerate(f.atms):
                    rows.append({**atm, 'probability': float(probabilities[i]),
                                 'reasons': explanations(f, i, model_name, matrix, contributions, bandwidth,
                                                         len(prior), expected, hours, fallback)})
                rows = sorted(enumerate(rows), key=lambda item: (-item[1]['probability'], -scores[item[0]], item[1]['id']))
                payload['models'][model_name][hours] = {
                    'model': model_name, 'window_hours': hours, 'fallback': fallback,
                    'atms': [r for _, r in rows],
                    'probability_note': 'Marginal estimates per ATM; several ATMs can cash out in one case. '
                                        'Heuristic models use recency/density weights and earlier training outcome rates. '
                                        'Independent XGBoost window models are not calibrated and need not be monotone across windows.',
                }
        predictions[case.complaint_id] = payload
        if case.prediction_time >= cutoff:
            bundles = {'models': models, 'bandwidth_km': bandwidth, 'training': meta}
    if output is not None:
        output.mkdir(parents=True, exist_ok=True)
        for hours, model in bundles.get('models', {}).items():
            if model is not None:
                model.save_model(output / f'xgb-{hours}h.ubj')
    atm_ids = [a['id'] for a in next(iter(features.values())).atms]
    # Runtime snapshots exclude outcomes after the current clock. CLI may show the full evaluation.
    trace_clock = datetime.fromisoformat(predictions[world.meta['demo_complaint_id']]['prediction_time'])
    reports = {clock.isoformat(): evaluate(test, predictions, atm_ids, scenario.seed, clock)
               for clock in (scenario.history_end, trace_clock)}
    metadata = {'train_start': scenario.start.isoformat(), 'test_start': cutoff.isoformat(),
                'test_end': (scenario.start + timedelta(days=90)).isoformat(),
                'train_cases_n': len(train), 'fitted_train_cases_n': bundles.get('training', {}).get('n', 0),
                'feature_names': FEATURE_NAMES, 'bandwidth_km': bundles.get('bandwidth_km', kde.DEFAULT_BANDWIDTH_KM),
                'bandwidth_candidates_km': list(kde.BANDWIDTHS_KM),
                'training_note': 'Training cases whose 24-hour outcomes were incomplete at day 70 are censored from fitting.'}
    return {'cases': predictions, 'evaluation': reports, 'full_evaluation': evaluate(test, predictions, atm_ids, scenario.seed),
            'metadata': metadata}
