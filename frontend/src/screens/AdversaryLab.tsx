import { useEffect, useState } from 'react';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  AdversaryCurvesResponse,
  AdversaryRunResult,
  api,
  Complaint,
} from '../api/client';
import { formatInr } from '../lib/format';

export function AdversaryLab() {
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [selectedCase, setSelectedCase] = useState<string>('');
  const [hardenedToggle, setHardenedToggle] = useState<boolean>(false);
  const [curves, setCurves] = useState<AdversaryCurvesResponse | null>(null);
  const [runResult, setRunResult] = useState<AdversaryRunResult | null>(null);
  const [loadingCurves, setLoadingCurves] = useState<boolean>(true);
  const [running, setRunning] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  // Load complaints and curves on mount
  useEffect(() => {
    let alive = true;
    api
      .complaints()
      .then((c) => {
        if (alive) {
          setComplaints(c);
          if (c.length > 0 && c[0]) setSelectedCase(c[0].id);
        }
      })
      .catch(() => {});

    api
      .adversaryCurves()
      .then((data) => {
        if (alive) setCurves(data);
      })
      .catch((err) => {
        if (alive) setError('Failed to load evasion curves: ' + String(err));
      })
      .finally(() => {
        if (alive) setLoadingCurves(false);
      });

    return () => {
      alive = false;
    };
  }, []);

  const handleRun = () => {
    setRunning(true);
    setError('');
    api
      .adversaryRun(selectedCase || undefined, hardenedToggle)
      .then((res) => {
        setRunResult(res);
      })
      .catch((err) => {
        setError('Simulation failed: ' + String(err));
      })
      .finally(() => {
        setRunning(false);
      });
  };

  // Prepare chart data merging baseline and hardened curves
  const chartData = curves
    ? curves.budgets.map((b, idx) => ({
        budget: b,
        budgetText: b === 0 ? '₹0' : `₹${b / 1000}k`,
        baselineRate: Number(((curves.baseline_curve[idx]?.detection_rate ?? 0) * 100).toFixed(1)),
        baselineCount: curves.baseline_curve[idx]?.detected_count ?? 0,
        hardenedRate: Number(((curves.hardened_curve[idx]?.detection_rate ?? 0) * 100).toFixed(1)),
        hardenedCount: curves.hardened_curve[idx]?.detected_count ?? 0,
      }))
    : [];

  const initialBaseRate = curves?.baseline_curve[0]?.detection_rate ?? 0;
  const initialHardRate = curves?.hardened_curve[0]?.detection_rate ?? 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-line pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold tracking-tight text-fg">Adversary Lab</h2>
            <span className="rounded bg-accent/15 px-2 py-0.5 text-xs font-semibold text-accent">
              Phase 5
            </span>
          </div>
          <p className="mt-1 text-sm text-fg-dim">
            Simulate how a criminal syndicate alters cash-out behavior to evade the top-5 predicted ATMs,
            and quantify evasion costs vs. model hardening.
          </p>
        </div>
      </div>

      {error && (
        <div className="rounded border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
          {error}
        </div>
      )}

      {/* KPI Telemetry Strip */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <div className="rounded border border-line bg-ink-900 p-4">
          <div className="text-xs font-medium uppercase tracking-wider text-fg-dim">
            Held-out Test Cases
          </div>
          <div className="mt-1 text-2xl font-bold text-fg">
            n = {curves?.test_cases_count ?? 17}
          </div>
          <div className="mt-0.5 text-xs text-fg-dim">Evaluation days 71–90</div>
        </div>

        <div className="rounded border border-line bg-ink-900 p-4">
          <div className="text-xs font-medium uppercase tracking-wider text-fg-dim">
            Baseline Detection @ ₹0
          </div>
          <div className="mt-1 text-2xl font-bold text-sky-400">
            {(initialBaseRate * 100).toFixed(1)}%
          </div>
          <div className="mt-0.5 text-xs text-fg-dim">Target 6h forecast window</div>
        </div>

        <div className="rounded border border-line bg-ink-900 p-4">
          <div className="text-xs font-medium uppercase tracking-wider text-fg-dim">
            Hardened Detection @ ₹0
          </div>
          <div className="mt-1 text-2xl font-bold text-accent">
            {(initialHardRate * 100).toFixed(1)}%
          </div>
          <div className="mt-0.5 text-xs text-fg-dim">+{( (initialHardRate - initialBaseRate) * 100 ).toFixed(1)}% institutional gain</div>
        </div>

        <div className="rounded border border-line bg-ink-900 p-4">
          <div className="text-xs font-medium uppercase tracking-wider text-fg-dim">
            Max Evasion Budget
          </div>
          <div className="mt-1 text-2xl font-bold text-warn">
            ₹25,000
          </div>
          <div className="mt-0.5 text-xs text-fg-dim">Syndicate budget frontier</div>
        </div>
      </div>

      {/* Main Evasion Cost Curve Section */}
      <div className="rounded border border-line bg-ink-900 p-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="text-base font-semibold text-fg">Evasion Cost Curve (spec §11)</h3>
            <p className="text-xs text-fg-dim">
              Detection rate over held-out test cases vs. criminal evasion budget. Non-increasing by construction.
            </p>
          </div>
          <div className="flex items-center gap-4 text-xs font-medium">
            <span className="flex items-center gap-1.5 text-sky-400">
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-sky-400" />
              Baseline XGBoost
            </span>
            <span className="flex items-center gap-1.5 text-accent">
              <span className="inline-block h-2.5 w-2.5 rounded-full bg-accent" />
              Hardened (Adversary-Augmented)
            </span>
          </div>
        </div>

        {loadingCurves ? (
          <div className="flex h-72 items-center justify-center text-sm text-fg-dim">
            Loading evasion curves…
          </div>
        ) : (
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                <XAxis dataKey="budgetText" stroke="#737373" fontSize={12} />
                <YAxis
                  stroke="#737373"
                  fontSize={12}
                  domain={[0, 100]}
                  tickFormatter={(v) => `${v}%`}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#171717',
                    borderColor: '#404040',
                    borderRadius: '0.375rem',
                    fontSize: '12px',
                    color: '#f5f5f5',
                  }}
                  formatter={(val: any, name: any) => [
                    `${val}%`,
                    name === 'baselineRate' ? 'Baseline Model' : 'Hardened Model',
                  ]}
                  labelFormatter={(lbl) => `Criminal Budget: ${lbl}`}
                />
                <Legend
                  wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }}
                  formatter={(value) =>
                    value === 'baselineRate' ? 'Baseline XGBoost' : 'Hardened (Adversary-Trained)'
                  }
                />
                <Line
                  type="monotone"
                  dataKey="baselineRate"
                  stroke="#38bdf8"
                  strokeWidth={2.5}
                  dot={{ r: 4, fill: '#38bdf8' }}
                  activeDot={{ r: 6 }}
                />
                <Line
                  type="monotone"
                  dataKey="hardenedRate"
                  stroke="#a855f7"
                  strokeWidth={2.5}
                  strokeDasharray="4 2"
                  dot={{ r: 4, fill: '#a855f7' }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        <div className="mt-4 rounded bg-ink-800/60 p-3 text-xs text-fg-dim">
          <strong className="text-fg">Methodology:</strong> For each test case, greedy search applies the move
          yielding the largest drop in detection probability per ₹ of cost (Switch ATM, 12h Delay, Extra Mule Hop,
          Split Amount). A case is counted as detected at budget <em className="text-fg font-serif">b</em> if it remains detected after the last move
          whose cumulative cost ≤ <em className="text-fg font-serif">b</em>. Retraining on training-period adversary maneuvers (days 1–70 only) elevates detection across the entire frontier.
        </div>
      </div>

      {/* Interactive Case Simulator */}
      <div className="rounded border border-line bg-ink-900 p-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-semibold text-fg">Interactive Syndicate Evasion Simulator</h3>
            <p className="text-xs text-fg-dim">
              Execute greedy search on an individual fraud case to inspect chronological evasion moves and economic costs.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <label className="flex items-center gap-2 text-xs text-fg-dim">
              Case:
              <select
                value={selectedCase}
                onChange={(e) => setSelectedCase(e.target.value)}
                className="rounded border border-line bg-ink-800 px-2 py-1 text-xs text-fg focus:outline-none focus:border-accent"
              >
                {complaints.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.id} ({formatInr(c.amount_inr)})
                  </option>
                ))}
              </select>
            </label>

            <label className="flex cursor-pointer items-center gap-2 text-xs font-medium text-fg">
              <input
                type="checkbox"
                checked={hardenedToggle}
                onChange={(e) => setHardenedToggle(e.target.checked)}
                className="rounded border-line bg-ink-800 text-accent focus:ring-0"
              />
              Test against Hardened Model
            </label>

            <button
              type="button"
              onClick={handleRun}
              disabled={running}
              className="rounded bg-accent px-3 py-1 text-xs font-semibold text-ink-950 transition hover:bg-accent/80 disabled:opacity-50"
            >
              {running ? 'Simulating Evasion…' : 'Run Evasion Search'}
            </button>
          </div>
        </div>

        {/* Results of Simulation */}
        {runResult ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <div className="rounded border border-line bg-ink-800 p-3">
                <div className="text-[10px] uppercase tracking-wider text-fg-dim">Initial State</div>
                <div className="mt-1 flex items-center gap-1.5">
                  <span
                    className={`inline-block h-2 w-2 rounded-full ${
                      runResult.initial_detected ? 'bg-danger' : 'bg-ok'
                    }`}
                  />
                  <span className="text-sm font-semibold text-fg">
                    {runResult.initial_detected ? 'DETECTED' : 'UNDETECTED'}
                  </span>
                </div>
                <div className="text-xs text-fg-dim">
                  Prob: {(runResult.initial_probability * 100).toFixed(1)}%
                </div>
              </div>

              <div className="rounded border border-line bg-ink-800 p-3">
                <div className="text-[10px] uppercase tracking-wider text-fg-dim">Final State</div>
                <div className="mt-1 flex items-center gap-1.5">
                  <span
                    className={`inline-block h-2 w-2 rounded-full ${
                      runResult.final_detected ? 'bg-danger' : 'bg-ok'
                    }`}
                  />
                  <span className="text-sm font-semibold text-fg">
                    {runResult.final_detected ? 'DETECTED' : 'EVADED'}
                  </span>
                </div>
                <div className="text-xs text-fg-dim">
                  Prob: {(runResult.final_probability * 100).toFixed(1)}%
                </div>
              </div>

              <div className="rounded border border-line bg-ink-800 p-3">
                <div className="text-[10px] uppercase tracking-wider text-fg-dim">Total Evasion Spend</div>
                <div className="mt-1 text-sm font-semibold text-warn">
                  {formatInr(runResult.total_cost)}
                </div>
                <div className="text-xs text-fg-dim">{runResult.moves_count} moves executed</div>
              </div>

              <div className="rounded border border-line bg-ink-800 p-3">
                <div className="text-[10px] uppercase tracking-wider text-fg-dim">Syndicate Margin Loss</div>
                <div className="mt-1 text-sm font-semibold text-fg">
                  {(
                    (runResult.total_cost /
                      (complaints.find((c) => c.id === runResult.complaint_id)?.amount_inr || 50000)) *
                    100
                  ).toFixed(1)}
                  %
                </div>
                <div className="text-xs text-fg-dim">Of stolen case proceeds</div>
              </div>
            </div>

            {/* Move Execution Log Table */}
            <div>
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wider text-fg-dim">
                Move-by-Move Execution Log
              </h4>
              {runResult.moves.length === 0 ? (
                <div className="rounded border border-line bg-ink-800/40 p-4 text-center text-xs text-fg-dim">
                  Case is already outside top-5 predicted ATMs. No adversary moves needed.
                </div>
              ) : (
                <div className="overflow-x-auto rounded border border-line">
                  <table className="w-full text-left text-xs">
                    <thead className="border-b border-line bg-ink-800 text-[11px] text-fg-dim uppercase">
                      <tr>
                        <th className="px-3 py-2">Step</th>
                        <th className="px-3 py-2">Move Type</th>
                        <th className="px-3 py-2">Tactic Description</th>
                        <th className="px-3 py-2">Step Cost</th>
                        <th className="px-3 py-2">Cumulative Spend</th>
                        <th className="px-3 py-2">Remaining Prob</th>
                        <th className="px-3 py-2">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line/40 bg-ink-900/60 font-mono">
                      {runResult.moves.map((m) => {
                        const badgeColor =
                          m.move === 'switch_atm'
                            ? 'bg-sky-500/15 text-sky-400 border-sky-500/30'
                            : m.move === 'delay'
                            ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                            : m.move === 'add_mule_hop'
                            ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                            : 'bg-purple-500/15 text-purple-400 border-purple-500/30';

                        return (
                          <tr key={m.step} className="hover:bg-ink-800/40">
                            <td className="px-3 py-2 font-bold text-fg">#{m.step}</td>
                            <td className="px-3 py-2 font-sans">
                              <span
                                className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase ${badgeColor}`}
                              >
                                {m.move.replace('_', ' ')}
                              </span>
                            </td>
                            <td className="px-3 py-2 font-sans text-fg">{m.description}</td>
                            <td className="px-3 py-2 text-fg">{formatInr(m.cost)}</td>
                            <td className="px-3 py-2 text-warn">{formatInr(m.cumulative_cost)}</td>
                            <td className="px-3 py-2 text-fg">
                              {(m.detection_prob * 100).toFixed(1)}%
                            </td>
                            <td className="px-3 py-2 font-sans">
                              {m.detected ? (
                                <span className="rounded bg-danger/15 px-1.5 py-0.5 text-[10px] font-semibold text-danger">
                                  IN TOP-5
                                </span>
                              ) : (
                                <span className="rounded bg-ok/15 px-1.5 py-0.5 text-[10px] font-semibold text-ok">
                                  EVADED
                                </span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="rounded border border-dashed border-line bg-ink-800/30 p-8 text-center text-xs text-fg-dim">
            Click <strong>"Run Evasion Search"</strong> above to simulate optimal criminal moves for the selected case.
          </div>
        )}
      </div>
    </div>
  );
}
