import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import cytoscape, { Core } from 'cytoscape';
import dagre from 'cytoscape-dagre';
import { api, Account, Trace, Transaction } from '../api/client';
import { formatInr, formatIst } from '../lib/format';

cytoscape.use(dagre);
const COLORS: Record<string, string> = { victim: '#4cc9f0', collector: '#ffb703', 'pass-through': '#ff5c7a', recipient: '#a8b6cf' };

function SourceTable({ records }: { records: Transaction[] }) {
  return <div className="table-scroll"><table><thead><tr><th>Record / time</th><th>Flow</th><th>Amount</th></tr></thead><tbody>
    {records.map(t => <tr key={t.id}><td>{t.id}<small>{formatIst(t.ts)}</small></td><td>{t.src} → {t.dst}<small>{t.channel}</small></td><td>{formatInr(t.amount_inr)}</td></tr>)}
  </tbody></table></div>;
}

export function CaseView() {
  const [params, setParams] = useSearchParams();
  const id = params.get('id');
  const [trace, setTrace] = useState<Trace>();
  const [account, setAccount] = useState<Account>();
  const [selected, setSelected] = useState('');
  const [error, setError] = useState('');
  const [accountError, setAccountError] = useState('');
  const [retry, setRetry] = useState(0);
  const [accountRetry, setAccountRetry] = useState(0);
  const [step, setStep] = useState<number | null>(null);
  const graphElement = useRef<HTMLDivElement>(null);
  const graph = useRef<Core>();
  useEffect(() => {
    let alive = true; setError(''); setTrace(undefined); setAccount(undefined); setSelected(''); setStep(null);
    if (id) void api.trace(id).then(value => { if (alive) setTrace(value); }).catch(() => { if (alive) setError('Case unavailable at the current clock. Return to the command center or retry.'); });
    else void api.complaints().then(rows => { if (alive && rows[0]) setParams({ id: rows[0].id }, { replace: true });
      else if (alive) setError('No reported complaints are available yet.'); }).catch(() => { if (alive) setError('Could not load complaints. Check the backend and retry.'); });
    return () => { alive = false; };
  }, [id, retry, setParams]);
  useEffect(() => {
    if (!selected) return;
    let alive = true; setAccount(undefined); setAccountError('');
    void api.account(selected).then(a => { if (alive) setAccount(a); }).catch(() => { if (alive) setAccountError('Could not load evidence. Select the account again to retry.'); });
    return () => { alive = false; };
  }, [selected, accountRetry]);
  useEffect(() => {
    if (!trace || !graphElement.current) return;
    const cy = cytoscape({ container: graphElement.current,
      elements: [...trace.nodes.map(n => ({ data: { id: n.id, label: `${n.id}\n${n.inferred_role}`, color: COLORS[n.inferred_role], hop: n.hop } })),
        ...trace.edges.map(e => ({ data: { id: e.id, source: e.src, target: e.dst, label: formatInr(e.traced_amount_inr ?? e.amount_inr), hop: e.hop } }))],
      style: [
        { selector: 'node', style: { 'background-color': 'data(color)', label: 'data(label)', color: '#e8eef7', 'font-size': 14, 'text-wrap': 'wrap', 'text-valign': 'bottom', 'text-margin-y': 12, width: 36, height: 36 } },
        { selector: 'edge', style: { width: 2, 'line-color': '#647996', 'target-arrow-color': '#647996', 'target-arrow-shape': 'triangle', 'curve-style': 'bezier', label: 'data(label)', color: '#e8eef7', 'font-size': 14, 'text-background-color': '#111a28', 'text-background-opacity': 1, 'text-background-padding': '4px' } },
        { selector: ':selected', style: { 'border-width': 4, 'border-color': '#fff' } },
        { selector: '.pending', style: { opacity: .12 } },
      ], layout: { name: 'dagre', rankDir: 'LR', nodeSep: 70, rankSep: 100 } as cytoscape.LayoutOptions,
      minZoom: .35, maxZoom: 2, wheelSensitivity: .2,
    });
    graph.current = cy;
    cy.on('tap', 'node', event => setSelected(event.target.id()));
    const resize = new ResizeObserver(() => { cy.resize(); cy.fit(undefined, 40); });
    resize.observe(graphElement.current);
    return () => { resize.disconnect(); cy.destroy(); graph.current = undefined; };
  }, [trace]);
  useEffect(() => {
    graph.current?.elements().forEach(e => { e.toggleClass('pending', step !== null && Number(e.data('hop')) > step); });
    if (step === null || !trace) return;
    const max = Math.max(0, ...trace.hop_order);
    const timer = window.setTimeout(() => setStep(step >= max ? null : step + 1), 1100);
    return () => window.clearTimeout(timer);
  }, [step, trace]);
  return <section className="investigation">
    <header className="page-heading"><div><h1>Case View</h1><p>Follow observed transfers. Roles and risk are inferred from evidence.</p></div><div className="actions">{id && <Link className="button" to={`/heatmap?id=${id}`}>Predict cash-out</Link>}<Link className="button" to="/command-center">All complaints</Link></div></header>
    {error && <p className="error" role="alert">{error} <button onClick={() => setRetry(r => r + 1)}>Retry</button></p>}
    {!trace ? !error && <p role="status">Loading case and evidence…</p> : <>
      <div className="case-summary"><strong>{trace.complaint.id}</strong><span>{formatInr(trace.complaint.amount_inr)} reported loss</span><span>As of {formatIst(trace.demo_clock)}</span></div>
      <div className="case-grid"><section className="panel graph-panel"><header><h2>Money trail</h2><div className="actions"><button onClick={() => setStep(step === null ? 0 : null)}>{step === null ? 'Play trace' : 'Stop animation'}</button><button onClick={() => graph.current?.fit(undefined, 40)}>Fit graph</button></div></header>
        <div className="legend">{Object.entries(COLORS).map(([role, color]) => <span key={role}><i style={{ background: color }} />{role}</span>)}</div>
        <div ref={graphElement} className="money-graph" aria-label="Observed money trail. Use the account buttons below for keyboard access." />
        <div className="account-buttons" aria-label="Select account">{trace.nodes.map(n => <button key={n.id} aria-pressed={selected === n.id} onClick={() => { setSelected(n.id); setAccountRetry(r => r + 1); }}>{n.id} · {n.inferred_role}</button>)}</div>
        <p className="map-caption">{trace.attribution_note}</p>
      </section><aside className="panel evidence-panel"><header><h2>Patterns & signals</h2></header>
        {Array.from(new Set(trace.patterns.map(p => p.rule))).map(rule => { const patterns = trace.patterns.filter(p => p.rule === rule); return <details key={rule} className="signal"><summary>{rule} <span>Why?</span></summary><p>{patterns[0]?.detail.reason}</p><p>Inferred accounts: {Array.from(new Set(patterns.flatMap(p => p.flagged))).join(', ')}</p><p>Select an account to inspect the source transactions.</p></details>; })}
        {!trace.patterns.length && <p className="map-caption">No configured patterns detected on this trace.</p>}
        <div className="account-detail"><h3>{selected || 'Inspect an account'}</h3>{!selected && <p>Select a node or account button to see its risk signals and source records.</p>}
          {selected && !account && !accountError && <p role="status">Loading account evidence…</p>}
          {accountError && <p role="alert" className="error">{accountError}<button onClick={() => setAccountRetry(r => r + 1)}>Retry evidence</button></p>}
          {account && <><p>{account.holder} · {account.bank}</p><p>Home district {account.home_district_id}</p><details className="signal"><summary>Account risk {(account.risk * 100).toFixed(1)}% <span>Why?</span></summary><p>Rule count plus positive structural and temporal contributions, divided by the observed population’s 99th percentile and capped at 100%. This is a relative score, not a probability.</p></details>
            {!account.signals.length && <p>No positive signals at this clock.</p>}
            {account.signals.map((s, index) => <details className="signal" key={`${s.name}-${index}`}><summary>{s.name} <span>Why?</span></summary><p>{s.reason}</p><SourceTable records={account.source_transactions.filter(t => s.tx_ids.includes(t.id))} /></details>)}
            <details className="signal"><summary>Observed account transactions ({account.transactions.length})</summary><SourceTable records={account.transactions} /></details></>}
        </div></aside></div>
      <details className="panel trace-records"><summary>Source records for this trace ({trace.edges.length})</summary><SourceTable records={trace.edges} /></details>
    </>}
  </section>;
}
