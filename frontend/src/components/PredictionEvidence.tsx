import { Link } from 'react-router-dom';
import { PredictedAtm, Prediction, PredictionReason } from '../api/client';
import { formatInr, formatIst } from '../lib/format';
import { sourceRecords } from '../lib/predictions';

function Evidence({ prediction, atm, reason }: { prediction: Prediction; atm: PredictedAtm; reason: PredictionReason }) {
  const records = sourceRecords(prediction, atm, reason);
  if (reason.source_group === 'training') return <div className="source-block"><p>Completed training cases: n={prediction.training.n}. Outcomes available through {prediction.training.latest_outcome_at ? formatIst(prediction.training.latest_outcome_at) : 'no observed outcomes'}.</p>
    <div className="source-links">{prediction.training.case_ids.map(id => <Link to={`/case?id=${id}`} key={id}>{id}</Link>)}</div></div>;
  if (reason.source_group === 'holders') return <div className="source-block"><p>Distance uses fictional district centres, not account addresses.</p>{prediction.evidence.accounts.filter(a => prediction.holder_accounts.includes(a.id)).map(a =>
    <p key={a.id}>{a.id} · {a.bank} · home district {a.home_district_id}</p>)}<p>ATM: {atm.id} · {atm.lat}, {atm.lng} · {atm.district_id}</p></div>;
  if (reason.source_group === 'complaint') return <div className="source-block"><p>{prediction.evidence.complaint.id} · reported {formatIst(prediction.evidence.complaint.reported_at)}.</p><p>Prediction time: {formatIst(prediction.prediction_time)}.</p></div>;
  return <div className="source-block">
    {reason.source_group === 'temporal' && <p>Temporal scores use the densest 48-hour window, normalized across eligible observed accounts in a population of {prediction.evidence.temporal_population_n}. The table contains supporting observed chain records.</p>}
    <p>{records.length} supporting records, all at or before prediction time.</p>
    {records.length > 0 && <div className="table-scroll"><table><thead><tr><th>Record / IST</th><th>Observed movement</th><th>Amount</th></tr></thead><tbody>
      {records.map(r => <tr key={r.id}><td>{r.id}<small>{formatIst(r.ts)}</small></td><td>{'atm_id' in r ? `${r.account_id} → ${r.atm_id}` : `${r.src} → ${r.dst}`}</td><td>{formatInr(r.amount_inr)}</td></tr>)}
    </tbody></table></div>}
  </div>;
}

export function PredictionEvidence({ prediction, atm }: { prediction: Prediction; atm: PredictedAtm }) {
  return <aside className="panel prediction-evidence"><header><div><h2>{atm.id}</h2><p>{atm.bank} · {atm.district_id}</p></div><strong className="forecast-probability">{(atm.probability * 100).toFixed(1)}%</strong></header>
    <p className="map-caption">Predicted cash-out within {prediction.window_hours} hours of {formatIst(prediction.prediction_time)}.</p>
    {atm.reasons.map((reason, i) => <details className="signal" key={`${atm.id}-${prediction.model}-${prediction.window_hours}-${i}`}><summary>Why? <span>{reason.feature ? reason.feature.replaceAll('_', ' ') : `Reason ${i + 1}`}</span></summary>
      <p>{reason.text}</p>{reason.contribution !== null && <p>Contribution: {reason.contribution >= 0 ? '+' : ''}{reason.contribution.toFixed(3)} log-odds relative to the model’s base score.</p>}
      <Evidence prediction={prediction} atm={atm} reason={reason} />
    </details>)}
    <details className="signal"><summary>Prediction method & limits</summary><p>{prediction.probability_note}</p><p>{prediction.training.method}</p>
      <p>Training n={prediction.training.n}; selected KDE bandwidth {prediction.training.bandwidth_km} km.</p><p>Terminal accounts are inferred from the observed trace. Direct neighbours extend the history used by the models.</p>
    </details>
  </aside>;
}
