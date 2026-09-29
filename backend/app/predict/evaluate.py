"""Time-split evaluation with case-level bootstrap intervals (never ATM-row bootstrap)."""
import numpy as np

from app.predict.cases import Case, MODELS, WINDOWS

TOP_K = 5
BOOTSTRAPS = 2000


def metrics(actual: list[set[str]], ranked: list[list[str]], seed: int) -> dict:
    n = len(actual)
    if not n:
        return {'n': 0, 'hit_rate': None, 'hit_rate_ci95': None, 'precision_at_5': None,
                'precision_ceiling': None, 'cases_with_cashout': 0}
    hit = np.array([bool(a.intersection(r[:TOP_K])) for a, r in zip(actual, ranked)], dtype=float)
    precision = np.array([len(a.intersection(r[:TOP_K])) / TOP_K for a, r in zip(actual, ranked)])
    bootstrap = np.random.default_rng(seed).choice(hit, size=(BOOTSTRAPS, n), replace=True).mean(axis=1)
    return {'n': n, 'hit_rate': float(hit.mean()), 'hit_rate_ci95': np.quantile(bootstrap, [.025, .975]).tolist(),
            'precision_at_5': float(precision.mean()),
            'precision_ceiling': float(np.mean([min(len(a), TOP_K) / TOP_K for a in actual])),
            'cases_with_cashout': sum(bool(a) for a in actual)}


def evaluate(test: list[Case], predictions: dict, atm_ids: list[str], seed: int, clock=None) -> dict:
    eligible = [c for c in test if clock is None or c.outcome_end <= clock]
    groups = ['overall', *sorted({c.strategy for c in test})]
    rows = []
    for group in groups:
        cases = [c for c in eligible if group == 'overall' or c.strategy == group]
        for hours in WINDOWS:
            actual = [{a for a, yes in zip(atm_ids, c.labels[hours]) if yes} for c in cases]
            for model in MODELS:
                ranked = [[a['id'] for a in predictions[c.complaint_id]['models'][model][hours]['atms']] for c in cases]
                rows.append({'strategy': group, 'window_hours': hours, 'model': model,
                             **metrics(actual, ranked, seed)})
    comparisons = []
    for group in groups:
        for hours in WINDOWS:
            by_model = {r['model']: r for r in rows if r['strategy'] == group and r['window_hours'] == hours}
            baseline, graph = by_model['baseline'], by_model['xgboost']
            better = graph['n'] > 0 and graph['hit_rate'] > baseline['hit_rate']
            comparisons.append({'strategy': group, 'window_hours': hours, 'n': graph['n'],
                                'beats_baseline': better,
                                'message': 'No completed test cases yet.' if not graph['n'] else
                                'Graph-aware XGBoost beats the baseline on hit rate in this sample.' if better else
                                'Graph-aware XGBoost does not beat the baseline on hit rate in this sample.'})
    return {'rows': rows, 'comparisons': comparisons, 'test_cases_total': len(test),
            'test_cases_available': len(eligible), 'pending_cases': len(test) - len(eligible),
            'bootstrap_replicates': BOOTSTRAPS, 'top_k': TOP_K,
            'note': 'Case-level 95% bootstrap intervals. Cases without cash-out in a window remain in n and count as misses. '
                    'Precision ceilings depend on the number of actual ATMs. Strategy names are evaluation ground truth only. '
                    'Only cases with a fully observed 24-hour outcome are included at this clock.'}


def print_table(report: dict) -> None:
    print('\nStrategy                 h  Model       n   Hit rate [95% CI]       P@5   Ceiling', flush=True)
    for row in report['rows']:
        ci = row['hit_rate_ci95']
        value = f"{row['hit_rate']:.3f} [{ci[0]:.3f}, {ci[1]:.3f}]" if ci else 'n/a'
        precision = f"{row['precision_at_5']:.3f}" if ci else 'n/a'
        ceiling = f"{row['precision_ceiling']:.3f}" if ci else 'n/a'
        print(f"{row['strategy']:<24} {row['window_hours']:>2} {row['model']:<10} {row['n']:>3}  {value:<23} {precision:>5} {ceiling:>7}", flush=True)
    for item in report['comparisons']:
        print(f"{item['strategy']} / {item['window_hours']}h / n={item['n']}: {item['message']}", flush=True)
