import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { api, Alert, Complaint } from '../api/client';
import { formatInr, formatIst } from '../lib/format';

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'bg-danger',
  high: 'bg-warn',
  medium: 'bg-accent',
};

const SEVERITY_TEXT: Record<string, string> = {
  critical: 'text-danger',
  high: 'text-warn',
  medium: 'text-accent',
};

export function Alerts() {
  const [params, setParams] = useSearchParams();
  const caseId = params.get('case');
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [selected, setSelected] = useState<Alert | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [generating, setGenerating] = useState(false);

  // Load alerts and complaints.
  useEffect(() => {
    let alive = true;
    setError('');
    void Promise.all([api.alerts(), api.complaints()]).then(([a, c]) => {
      if (!alive) return;
      setAlerts(a);
      setComplaints(c);
      setLoading(false);
    }).catch(() => { if (alive) { setError('Could not load alerts.'); setLoading(false); } });
    return () => { alive = false; };
  }, []);

  const handleGenerate = () => {
    if (!caseId) return;
    setGenerating(true);
    void api.generateAlerts(caseId).then(() => {
      return api.alerts();
    }).then(a => {
      setAlerts(a);
      setGenerating(false);
    }).catch(() => { setError('Failed to generate alerts.'); setGenerating(false); });
  };

  const handleAck = (alertId: string) => {
    void api.ackAlert(alertId).then(updated => {
      setAlerts(prev => prev.map(a => a.id === alertId ? updated : a));
      if (selected?.id === alertId) setSelected(updated);
    }).catch(() => setError('Failed to acknowledge alert.'));
  };

  const filteredAlerts = caseId ? alerts.filter(a => a.complaint_id === caseId) : alerts;
  const triggered = filteredAlerts.filter(a => a.status === 'triggered').length;
  const acknowledged = filteredAlerts.filter(a => a.status === 'acknowledged').length;

  return <section className="investigation alerts-screen">
    <header className="page-heading">
      <div>
        <h1>Alerts</h1>
        <p>Mock alerts to police and banks, with delivery status.</p>
      </div>
      <div className="actions">
        {caseId && <Link className="button" to={`/case?id=${caseId}`}>View money trail</Link>}
        {caseId && <Link className="button" to={`/blocking?id=${caseId}`}>Fund blocking</Link>}
      </div>
    </header>

    <div className="prediction-controls">
      <label>Case
        <select value={caseId ?? ''} onChange={e => { const v = e.target.value; setParams(v ? { case: v } : {}, { replace: true }); }}>
          <option value="">All cases</option>
          {complaints.map(c => <option key={c.id} value={c.id}>{c.id} · {formatInr(c.amount_inr)}</option>)}
        </select>
      </label>
      {caseId && (
        <button className="primary" onClick={handleGenerate} disabled={generating}>
          {generating ? 'Generating…' : 'Generate alerts for this case'}
        </button>
      )}
    </div>

    {error && <div role="alert" className="error">{error}</div>}

    <div className="alert-kpi-strip kpi-strip" style={{ gridTemplateColumns: 'repeat(3,1fr)', marginTop: 20 }}>
      <div><dt>Total alerts</dt><dd>{filteredAlerts.length}</dd></div>
      <div><dt>Triggered</dt><dd className="text-danger">{triggered}</dd></div>
      <div><dt>Acknowledged</dt><dd className="text-ok">{acknowledged}</dd></div>
    </div>

    {loading && <p role="status">Loading alerts…</p>}

    {!loading && <div className="alerts-grid">
      <section className="panel alert-feed-panel">
        <header><h2>Alert feed</h2><span>{filteredAlerts.length} alert{filteredAlerts.length !== 1 ? 's' : ''}</span></header>
        <div className="alert-feed">
          {filteredAlerts.length === 0 && <p className="alert-empty">No alerts yet.{caseId ? ' Generate alerts for the selected case.' : ' Select a case and generate alerts.'}</p>}
          {filteredAlerts.map(alert => (
            <button key={alert.id}
              className={`alert-row${selected?.id === alert.id ? ' alert-row-active' : ''}`}
              aria-pressed={selected?.id === alert.id}
              onClick={() => setSelected(alert)}>
              <div className="alert-row-header">
                <span className={`alert-severity ${SEVERITY_COLORS[alert.severity]}`}>{alert.severity}</span>
                <span className="alert-status">{alert.status === 'acknowledged' ? '✓ Acknowledged' : '● Triggered'}</span>
              </div>
              <strong>{alert.title}</strong>
              <p>{alert.description}</p>
              <small>{formatIst(alert.created_at)} · {alert.complaint_id}</small>
            </button>
          ))}
        </div>
      </section>

      {selected && <section className="panel alert-detail-panel">
        <header><h2>Alert details</h2><span>{selected.id}</span></header>
        <div className="alert-detail">
          <div className="alert-detail-meta">
            <span><strong>Severity</strong><br /><span className={SEVERITY_TEXT[selected.severity]}>{selected.severity.toUpperCase()}</span></span>
            <span><strong>Target</strong><br />{selected.target_type === 'ATM' ? `${selected.target_id} (${selected.target_bank})` : selected.target_id}</span>
            <span><strong>Probability</strong><br />{(selected.probability * 100).toFixed(1)}%</span>
            <span><strong>Status</strong><br />{selected.status}</span>
          </div>

          <h3>Why this alert?</h3>
          <p>{selected.description}</p>
          {selected.window_hours > 0 && <p className="alert-window">Cash-out predicted within <strong>{selected.window_hours}h</strong> window using <strong>{selected.model}</strong> model.</p>}

          <h3>Mock delivery log</h3>
          <p className="mock-delivery-label">Mock delivery · no real messages sent</p>
          <table className="delivery-table">
            <thead><tr><th>Channel</th><th>Recipient</th><th>Status</th><th>Time</th></tr></thead>
            <tbody>
              {selected.channels.map((ch, i) => (
                <tr key={i}>
                  <td><span className="channel-badge">{ch.type.toUpperCase()}</span> {ch.label}</td>
                  <td>{ch.recipient}</td>
                  <td className="text-ok">{ch.status}</td>
                  <td>{formatIst(ch.delivered_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="alert-actions" style={{ marginTop: 20 }}>
            {selected.status === 'triggered' && (
              <button className="primary" onClick={() => handleAck(selected.id)}>Acknowledge alert</button>
            )}
            {selected.status === 'acknowledged' && (
              <span className="text-ok">✓ Acknowledged at {formatIst(selected.acknowledged_at!)}</span>
            )}
            <Link className="button" to={`/heatmap?id=${selected.complaint_id}`}>View heatmap</Link>
          </div>
        </div>
      </section>}
    </div>}
  </section>;
}
