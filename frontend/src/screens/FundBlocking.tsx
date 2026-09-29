import { CSSProperties, useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { api, BlockRecommendation, Complaint, FreezeSimulation } from '../api/client';
import { formatInr } from '../lib/format';

export function FundBlocking() {
  const [params, setParams] = useSearchParams();
  const id = params.get('id');
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [rec, setRec] = useState<BlockRecommendation | null>(null);
  const [sim, setSim] = useState<FreezeSimulation | null>(null);
  const [loading, setLoading] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [error, setError] = useState('');
  const [checkedAccounts, setCheckedAccounts] = useState<Set<string>>(new Set());

  // Load complaints list.
  useEffect(() => {
    void api.complaints().then(setComplaints).catch(() => setError('Failed to load complaints.'));
  }, []);

  // Load blocking recommendations when case changes.
  useEffect(() => {
    if (!id) { setRec(null); setSim(null); return; }
    let alive = true;
    setLoading(true); setError(''); setSim(null);
    void api.blockRecommendations(id).then(r => {
      if (!alive) return;
      setRec(r);
      setCheckedAccounts(new Set(r.recommended_accounts.map(a => a.id)));
    }).catch(() => {
      if (alive) { setRec(null); setError('Fund blocking analysis unavailable at this demo clock. Start the demo first.'); }
    }).finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [id]);

  const handleSimulate = () => {
    if (!id || checkedAccounts.size === 0) return;
    setSimulating(true); setError('');
    void api.simulateFreeze(id, [...checkedAccounts]).then(result => {
      setSim(result);
    }).catch(() => setError('Simulation failed.')).finally(() => setSimulating(false));
  };

  const toggleAccount = (aid: string) => {
    setCheckedAccounts(prev => {
      const next = new Set(prev);
      if (next.has(aid)) next.delete(aid); else next.add(aid);
      return next;
    });
    setSim(null); // Reset simulation when selection changes.
  };

  const beforeInr = sim?.money_reachable_before_inr ?? rec?.money_reachable_before_inr ?? 0;
  const afterInr = sim?.money_reachable_after_inr ?? rec?.money_reachable_after_inr ?? 0;
  const preventedInr = sim?.prevented_inr ?? rec?.prevented_inr ?? 0;
  const preventedPct = sim?.prevented_pct ?? rec?.prevented_pct ?? 0;
  const barBefore = beforeInr > 0 ? 100 : 0;
  const barAfter = beforeInr > 0 ? (afterInr / beforeInr) * 100 : 0;

  return <section className="investigation blocking-screen">
    <header className="page-heading">
      <div>
        <h1>Fund Blocking</h1>
        <p>Which accounts to freeze, and how much money that stops.</p>
      </div>
      <div className="actions">
        {id && <Link className="button" to={`/case?id=${id}`}>View money trail</Link>}
        {id && <Link className="button" to={`/alerts?case=${id}`}>View alerts</Link>}
      </div>
    </header>

    <div className="prediction-controls">
      <label>Case
        <select value={id ?? ''} onChange={e => setParams(e.target.value ? { id: e.target.value } : {}, { replace: true })}>
          <option value="">Choose a case</option>
          {complaints.map(c => <option key={c.id} value={c.id}>{c.id} · {formatInr(c.amount_inr)}</option>)}
        </select>
      </label>
    </div>

    {error && <div role="alert" className="error">{error}</div>}
    {loading && <p role="status">Analysing money flow for freeze recommendations…</p>}

    {rec && <div className="blocking-grid">
      {/* Money flow bar chart */}
      <section className="panel blocking-impact-panel">
        <header>
          <h2>Impact analysis</h2>
          <span>{sim ? 'Custom freeze simulation' : 'Min-cut recommendation'}</span>
        </header>
        <div className="blocking-impact">
          <div className="impact-bars">
            <div className="impact-bar-row">
              <span className="impact-bar-label">Before freeze</span>
              <div className="impact-bar-track">
                <div className="impact-bar impact-bar-before" style={{ '--impact-scale': barBefore / 100 } as CSSProperties} aria-hidden="true" />
              </div>
              <span className="impact-bar-value">{formatInr(beforeInr)}</span>
            </div>
            <div className="impact-bar-row">
              <span className="impact-bar-label">After freeze</span>
              <div className="impact-bar-track">
                <div className="impact-bar impact-bar-after" style={{ '--impact-scale': barAfter / 100 } as CSSProperties} aria-hidden="true" />
              </div>
              <span className="impact-bar-value">{formatInr(afterInr)}</span>
            </div>
          </div>
          <div className="impact-summary">
            <div className="impact-stat impact-stat-main">
              <dt>Money stopped</dt>
              <dd className="text-ok">{formatInr(preventedInr)}</dd>
            </div>
            <div className="impact-stat">
              <dt>Prevented</dt>
              <dd className="text-ok">{(preventedPct * 100).toFixed(1)}%</dd>
            </div>
            <div className="impact-stat">
              <dt>Accounts frozen</dt>
              <dd>{checkedAccounts.size}</dd>
            </div>
          </div>
        </div>
      </section>

      {/* Recommended accounts */}
      <section className="panel blocking-accounts-panel">
        <header>
          <h2>Freeze recommendations</h2>
          <span>Select accounts to freeze</span>
        </header>
        <div className="blocking-accounts">
          {rec.recommended_accounts.map(acct => (
            <label key={acct.id} className={`blocking-account-row${checkedAccounts.has(acct.id) ? ' blocking-account-checked' : ''}`}>
              <input type="checkbox" checked={checkedAccounts.has(acct.id)} onChange={() => toggleAccount(acct.id)} />
              <div className="blocking-account-info">
                <div className="blocking-account-header">
                  <strong>{acct.id}</strong>
                  {acct.inferred_role && <span className="blocking-role">{acct.inferred_role}</span>}
                  {acct.bank && <span className="blocking-bank">{acct.bank}</span>}
                </div>
                <p>{acct.reason}</p>
                <div className="blocking-account-meta">
                  {acct.hop !== undefined && <span>Hop {acct.hop}</span>}
                  {acct.risk !== undefined && <span>Risk {(acct.risk * 100).toFixed(0)}%</span>}
                  {acct.home_district_id && <span>{acct.home_district_id}</span>}
                </div>
              </div>
            </label>
          ))}
        </div>
        <div className="blocking-simulate-bar">
          <button className="primary" onClick={handleSimulate} disabled={simulating || checkedAccounts.size === 0}>
            {simulating ? 'Simulating…' : `Simulate freeze (${checkedAccounts.size} account${checkedAccounts.size !== 1 ? 's' : ''})`}
          </button>
          {sim && <span className="text-ok">✓ Simulation complete</span>}
        </div>
      </section>
    </div>}

    {!id && !loading && <p role="status">Select a case to see freeze recommendations.</p>}
  </section>;
}
