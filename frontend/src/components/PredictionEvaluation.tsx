import { Evaluation, EvaluationRow, ModelName } from '../api/client';
import { formatIst } from '../lib/format';

const NAMES: Record<ModelName, string> = { baseline: 'Recency baseline', kde: 'Spatial KDE', xgboost: 'Graph-aware XGBoost' };
const percent = (value: number | null) => value === null ? '—' : `${(value * 100).toFixed(1)}%`;

function Metric({ row }: { row: EvaluationRow | undefined }) {
  if (!row || !row.n) return <span>No completed cases · n=0</span>;
  return <><strong>{percent(row.hit_rate)} hit rate</strong><span>95% CI {percent(row.hit_rate_ci95?.[0] ?? null)}–{percent(row.hit_rate_ci95?.[1] ?? null)} · n={row.n}</span>
    <small>P@5 {percent(row.precision_at_5)} / ceiling {percent(row.precision_ceiling)}</small><small>{row.cases_with_cashout} of {row.n} cases cashed out in this window</small></>;
}

export function PredictionEvaluation({ report, hours }: { report: Evaluation; hours: number }) {
  const rows = report.rows.filter(row => row.window_hours === hours);
  const groups = [...new Set(rows.map(row => row.strategy))];
  const models: ModelName[] = ['baseline', 'kde', 'xgboost'];
  return <section className="panel evaluation-panel"><header><div><h2>Held-out evaluation · {hours}h window</h2><p>Top-{report.top_k} hit rate, with the baseline beside both models.</p></div><span>Available test cases n={report.test_cases_available}</span></header>
    <div className="table-scroll evaluation-table"><table><thead><tr><th>Evaluation group</th>{models.map(m => <th key={m}>{NAMES[m]}</th>)}</tr></thead><tbody>
      {groups.map(group => <tr key={group}><th>{group === 'overall' ? 'All strategies' : group.replaceAll('_', ' ')}<small>{report.comparisons.find(c => c.strategy === group && c.window_hours === hours)?.message}</small></th>
        {models.map(model => <td key={model}><Metric row={rows.find(r => r.model === model && r.strategy === group)} /></td>)}
      </tr>)}
    </tbody></table></div>
    <details className="signal"><summary>Evaluation protocol & sample size</summary><p>Training: {formatIst(report.train_start)} up to {formatIst(report.test_start)} (exclusive). Training cases n={report.train_cases_n}; fully observed fitting cases n={report.fitted_train_cases_n}.</p>
      <p>Test prediction times: {formatIst(report.test_start)} up to {formatIst(report.test_end)} (exclusive). {report.pending_cases} of {report.test_cases_total} scheduled cases still await a complete outcome at this clock.</p>
      <p>{report.note}</p><p>{report.training_note} Intervals use {report.bootstrap_replicates.toLocaleString('en-IN')} deterministic bootstrap samples.</p>
      <p>Bandwidth {report.bandwidth_km} km was selected using training cases only. Candidates: {report.bandwidth_candidates_km.join(', ')} km.</p>
    </details>
  </section>;
}
