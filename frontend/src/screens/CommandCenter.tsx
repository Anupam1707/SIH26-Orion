import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { GeoJSON, MapContainer } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { api, Complaint, Summary } from '../api/client';
import { formatInr, formatIst } from '../lib/format';

export function CommandCenter() {
  const [data, setData] = useState<{ summary: Summary; complaints: Complaint[]; districts: GeoJSON.FeatureCollection }>();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const load = () => { setError(''); void Promise.all([api.summary(), api.complaints(), api.districts()])
    .then(([summary, complaints, districts]) => setData({ summary, complaints, districts }))
    .catch(() => setError('Could not load the command center. Check the backend and retry.')); };
  useEffect(load, []);
  async function preview() {
    setBusy(true); setError('');
    try { const demo = await api.start(); navigate(`/case?id=${demo.complaint_id}`); }
    catch { setError('Could not open the demo case. Check the backend and retry.'); }
    finally { setBusy(false); }
  }
  async function reset() {
    setBusy(true);
    try { await api.reset(); load(); } catch { setError('Reset failed. Retry when the backend is available.'); }
    finally { setBusy(false); }
  }
  return <section className="investigation">
    <header className="page-heading"><div><h1>Command Center</h1><p>Observed complaints and money movement across the simulated districts.</p></div>
      <div className="actions"><button className="primary" onClick={preview} disabled={busy}>Open demo trace</button>
        {data?.summary.demo_running && <button onClick={reset} disabled={busy}>Reset history</button>}</div></header>
    {error && <div role="alert" className="error">{error} <button onClick={load}>Retry</button></div>}
    {!data ? <p role="status">Loading observed records…</p> : <>
      <p className="clock">As of {formatIst(data.summary.demo_clock)} · Demo trace preview advances the clock to the completed transfer chain.</p>
      <dl className="kpi-strip">
        <div><dt>Reported complaints</dt><dd>{data.summary.complaints.toLocaleString('en-IN')}</dd></div>
        <div><dt>Reported loss</dt><dd>{formatInr(data.summary.reported_amount_inr)}</dd></div>
        <div><dt>Observed transfers</dt><dd>{data.summary.observed_transactions.toLocaleString('en-IN')}</dd></div>
        <div><dt>Accounts with patterns</dt><dd>{data.summary.accounts_with_patterns.toLocaleString('en-IN')}</dd></div>
      </dl>
      <div className="command-grid"><section className="panel"><header><h2>Complaint feed</h2><span>Newest reported first</span></header>
        <div className="complaint-feed">{data.complaints.length === 0 ? <p>No complaints reported at this time.</p> : data.complaints.map(c =>
          <Link className="complaint-row" to={`/case?id=${c.id}`} key={c.id}>
            <div><strong>{c.id}</strong><p>{c.description}</p><small>{formatIst(c.reported_at)} · {c.district_id}</small></div>
            <span className="money">{formatInr(c.amount_inr)}<small>Trace case →</small></span>
          </Link>)}</div></section>
        <section className="panel"><header><h2>District overview</h2></header><p className="map-caption">Fictional boundaries · darker fill indicates more reported complaints</p>
          <MapContainer bounds={L.geoJSON(data.districts).getBounds()} className="district-map" scrollWheelZoom={false} attributionControl={false}>
            <GeoJSON data={data.districts} style={f => {
              const count = data.complaints.filter(c => c.district_id === f?.properties?.id).length;
              return { color: '#4cc9f0', weight: 2, fillColor: '#4cc9f0', fillOpacity: .12 + .55 * count / Math.max(data.complaints.length, 1) };
            }} onEachFeature={(f, layer) => {
              const count = data.complaints.filter(c => c.district_id === f.properties?.id).length;
              layer.bindTooltip(`${f.properties?.name}: ${count} complaints`, { permanent: true, direction: 'center' });
            }} />
          </MapContainer><p className="map-caption">Select a complaint to inspect its observed chain and supporting records.</p></section>
      </div></>}
  </section>;
}
