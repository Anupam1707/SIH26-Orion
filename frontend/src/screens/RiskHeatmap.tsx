import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { CircleMarker, GeoJSON, MapContainer, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { api, Evaluation, ModelName, Prediction, PredictionCase } from '../api/client';
import { PredictionEvidence } from '../components/PredictionEvidence';
import { PredictionEvaluation } from '../components/PredictionEvaluation';
import { filterAtms, probabilityColor } from '../lib/predictions';
import { formatInr, formatIst } from '../lib/format';

const MODEL_NAMES: Record<ModelName, string> = { baseline: 'Recency baseline', kde: 'Spatial KDE', xgboost: 'Graph-aware XGBoost' };

function MapResize() {
  const map = useMap();
  useEffect(() => { const observer = new ResizeObserver(() => map.invalidateSize()); observer.observe(map.getContainer()); return () => observer.disconnect(); }, [map]);
  return null;
}

export function RiskHeatmap() {
  const [params, setParams] = useSearchParams();
  const id = params.get('id');
  const [context, setContext] = useState<{ cases: PredictionCase[]; districts: GeoJSON.FeatureCollection; report: Evaluation }>();
  const [prediction, setPrediction] = useState<Prediction>();
  const [model, setModel] = useState<ModelName>('baseline');
  const [hours, setHours] = useState(6);
  const [threshold, setThreshold] = useState(0);
  const [selected, setSelected] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    let alive = true; setError('');
    void Promise.all([api.predictionCases(), api.districts(), api.evaluation()]).then(([cases, districts, report]) => {
      if (!alive) return;
      setContext({ cases, districts, report });
      if (!id) { const first = cases.find(c => c.ready); if (first) setParams({ id: first.id }, { replace: true }); }
    }).catch(() => { if (alive) setError('Could not load prediction data. Check the backend and retry.'); });
    return () => { alive = false; };
  }, [retry, id, setParams]);
  useEffect(() => {
    if (!id) return;
    let alive = true; setLoading(true); setError('');
    void api.predictions(id, model, hours).then(result => {
      if (alive) { setPrediction(result); setSelected(''); }
    }).catch(() => { if (alive) { setPrediction(undefined); setError('This forecast is unavailable at the current demo clock. Choose a ready case or retry.'); } })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [id, model, hours, retry]);
  const filtered = useMemo(() => filterAtms(prediction?.atms ?? [], threshold), [prediction, threshold]);
  const active = filtered.find(a => a.id === selected) ?? filtered[0];
  const bounds = useMemo(() => context ? L.geoJSON(context.districts).getBounds() : undefined, [context]);
  return <section className="investigation heatmap-screen">
    <header className="page-heading"><div><h1>Risk Heatmap</h1><p>Where the case’s money may become cash. Compare models, then inspect the evidence.</p></div>
      <Link className="button" to={id ? `/case?id=${id}` : '/command-center'}>View money trail</Link></header>
    <div className="prediction-controls">
      <label>Case<select value={id ?? ''} onChange={e => setParams({ id: e.target.value })} disabled={!context}>
        {!id && <option value="">Choose a reported case</option>}{context?.cases.map(c => <option key={c.id} value={c.id} disabled={!c.ready}>{c.id} · {formatInr(c.amount_inr)}{!c.ready ? ' · awaiting transfers' : ''}</option>)}
      </select></label>
      <label>Prediction model<select value={model} onChange={e => setModel(e.target.value as ModelName)}>{Object.entries(MODEL_NAMES).map(([value, name]) => <option key={value} value={value}>{name}</option>)}</select></label>
      <label>Cash-out window<select value={hours} onChange={e => setHours(Number(e.target.value))}>{[2, 6, 24].map(h => <option key={h} value={h}>Next {h} hours</option>)}</select></label>
      <label className="threshold-control">Minimum probability: {threshold}%<input aria-label="Minimum probability" type="range" min="0" max="100" step="1" value={threshold} onChange={e => setThreshold(Number(e.target.value))} /></label>
    </div>
    {error && <div role="alert" className="error">{error} <button onClick={() => setRetry(r => r + 1)}>Retry</button></div>}
    {loading && <p role="status" className="clock">Updating forecast…{prediction ? ' The previous forecast remains visible until loading completes.' : ''}</p>}
    {!prediction && !loading && !error && <p role="status">{context ? 'No ready forecast at this clock. Open the demo trace from Command Center.' : 'Loading the map and evaluation…'}</p>}
    {prediction && context && bounds && <>
      <div className="forecast-context"><strong>{prediction.complaint_id} · {MODEL_NAMES[prediction.model]} · {prediction.window_hours}h</strong><span>Prediction as of {formatIst(prediction.prediction_time)}</span><span>{filtered.length} of {prediction.atms.length} ATMs shown</span></div>
      {prediction.fallback && <p className="fallback-notice" role="status">{prediction.fallback}</p>}
      <div className="forecast-grid" aria-busy={loading}>
        <section className="panel forecast-map-panel"><header><h2>Predicted ATM cash-out</h2><span>Fictional map · no external tiles</span></header>
          <MapContainer bounds={bounds} className="forecast-map" scrollWheelZoom={false} attributionControl={false}>
            <MapResize /><GeoJSON data={context.districts} style={{ color: '#647996', weight: 1, fillColor: '#263449', fillOpacity: .28 }} onEachFeature={(feature, layer) => layer.bindTooltip(String(feature.properties?.name ?? ''), { sticky: true })} />
            {filtered.map(atm => <CircleMarker key={atm.id} center={[atm.lat, atm.lng]} radius={6 + 22 * Math.sqrt(atm.probability)} pathOptions={{ color: probabilityColor(atm.probability), fillColor: probabilityColor(atm.probability), fillOpacity: .15 + .5 * atm.probability, weight: active?.id === atm.id ? 3 : 1.5, dashArray: '4 3' }} eventHandlers={{ click: () => setSelected(atm.id) }}>
              <Tooltip>{atm.id} · {(atm.probability * 100).toFixed(1)}% · {prediction.window_hours}h</Tooltip>
            </CircleMarker>)}
          </MapContainer>
          <div className="forecast-legend"><span>Dashed circles = predictions</span><span><i style={{ background: probabilityColor(0) }} />Lower probability</span><span><i style={{ background: probabilityColor(1) }} />Higher probability</span></div>
          <p className="map-caption">Circle size and colour reflect each ATM’s marginal probability. Several ATMs may be used by one case.</p>
        </section>
        <div className="forecast-side"><section className="panel atm-ranking"><header><h2>ATM ranking</h2><span>By probability</span></header>
          {!filtered.length ? <div className="empty-forecast"><p>No ATM meets the {threshold}% threshold.</p><button onClick={() => setThreshold(0)}>Show all ATMs</button></div> : <ol>{filtered.map((atm, rank) => <li key={atm.id}><button aria-pressed={active?.id === atm.id} onClick={() => setSelected(atm.id)}>
            <span className="rank-index">{rank + 1}</span><span><strong>{atm.id}</strong><small>{atm.bank} · {atm.district_id}</small></span><span className="rank-probability">{(atm.probability * 100).toFixed(1)}%<small>Why?</small></span>
          </button></li>)}</ol>}
        </section>{active && <PredictionEvidence prediction={prediction} atm={active} />}</div>
      </div>
    </>}
    {context && <PredictionEvaluation report={context.report} hours={hours} />}
  </section>;
}
