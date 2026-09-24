import React, { useState } from 'react';
import { 
  Flame, 
  ArrowRight, 
  AlertTriangle, 
  TrendingUp, 
  Clock, 
  ShieldCheck, 
  HelpCircle,
  GitBranch,
  Split,
  ChevronRight
} from 'lucide-react';
import { formatINR } from '../utils/crypto';

export default function TypologyStories({ 
  typologies, 
  topologicalBridge, 
  onSelectTypology, 
  selectedTypologyId,
  oddballList,
  temporalList
}) {
  const [activeTab, setActiveTab] = useState('stories'); // 'stories' | 'oddball' | 'temporal'

  return (
    <div className="flex flex-col h-full bg-[#0a0e1a] overflow-hidden">
      {/* Sub-Header Tabs */}
      <div className="px-6 py-3 border-b border-slate-800 bg-[#0e1629]/90 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Flame className="w-5 h-5 text-rose-500" />
          <h2 className="text-base font-bold text-white tracking-tight">
            Typology Detection & Anomaly Center
          </h2>
        </div>

        <div className="flex items-center gap-1 bg-slate-900/80 p-1 rounded-lg border border-slate-800">
          <button
            onClick={() => setActiveTab('stories')}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition-all ${
              activeTab === 'stories' ? 'bg-sky-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            Planted Ground Truth Typologies ({typologies?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('oddball')}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition-all ${
              activeTab === 'oddball' ? 'bg-sky-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            OddBall Structural Anomalies (Top 20)
          </button>
          <button
            onClick={() => setActiveTab('temporal')}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition-all ${
              activeTab === 'temporal' ? 'bg-sky-500 text-white shadow-sm' : 'text-slate-400 hover:text-white'
            }`}
          >
            48h Temporal Bursts (Z-Scored)
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {activeTab === 'stories' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Special Highlight Card: Topological Bridge A00013 <-> A00055 */}
            {topologicalBridge && (
              <div 
                onClick={() => onSelectTypology({
                  typology_id: 'TOPOLOGICAL_BRIDGE',
                  pattern_type: 'INFERRED_TOPOLOGICAL_BRIDGE',
                  title: topologicalBridge.title,
                  narrative: topologicalBridge.warning_message,
                  honesty_notes: 'Demonstrates why graph paths are NOT proof of a money trail. Explicit/Inferred/Predicted taxonomy prevents judicial error.',
                  nodes: topologicalBridge.nodes,
                  edges: topologicalBridge.edges,
                  warning: {
                    title: topologicalBridge.warning_title,
                    message: topologicalBridge.warning_message
                  }
                })}
                className={`p-4 rounded-xl border cursor-pointer transition-all hover:scale-[1.01] flex flex-col justify-between ${
                  selectedTypologyId === 'TOPOLOGICAL_BRIDGE' 
                    ? 'bg-amber-950/40 border-amber-500 shadow-xl shadow-amber-500/10' 
                    : 'bg-[#0f172a]/80 border-amber-500/40 hover:border-amber-500/80'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                      Headline Scientific Finding
                    </span>
                    <span className="text-xs font-bold text-amber-400 mono">Length-5 Path</span>
                  </div>

                  <h3 className="text-sm font-bold text-white mb-1.5 flex items-center gap-1.5">
                    <Split className="w-4 h-4 text-amber-400" />
                    <span>Mule (A00013) ↔ Scatter (A00055) Path</span>
                  </h3>

                  <p className="text-xs text-slate-300 leading-relaxed line-clamp-3">
                    Topological connection linking mule collector P00231 to scatter syndicate head P02240 across pass-through accounts. 
                  </p>

                  <div className="mt-3 p-2.5 rounded-lg bg-amber-900/30 border border-amber-500/30 text-[11px] text-amber-200 flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    <div>
                      <strong className="block text-amber-300">Non-Chronological Timestamps:</strong>
                      Timestamps occur out of order (Sep 2024 ➔ Jun 2025 ➔ Feb 2024). Governed as <em>Inferred Topological Reachability</em>, NOT a Money Trail.
                    </div>
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs font-semibold text-amber-400">
                  <span>Load Interactive Subgraph</span>
                  <ChevronRight className="w-4 h-4" />
                </div>
              </div>
            )}

            {/* Ground Truth Planted Typologies */}
            {typologies?.map((item) => {
              const isSelected = selectedTypologyId === item.typology_id;
              const isMule = item.pattern_type === 'MULE_FAN_IN';
              const isScatter = item.pattern_type === 'SCATTER_GATHER';
              const isStructuring = item.pattern_type === 'STRUCTURING';

              return (
                <div
                  key={item.typology_id}
                  onClick={() => onSelectTypology(item)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all hover:scale-[1.01] flex flex-col justify-between ${
                    isSelected
                      ? 'bg-sky-950/40 border-sky-500 shadow-xl shadow-sky-500/10'
                      : 'bg-[#0f172a]/80 border-slate-800 hover:border-slate-700'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border ${
                        isMule 
                          ? 'bg-rose-500/15 text-rose-300 border-rose-500/30' 
                          : (isScatter 
                              ? 'bg-amber-500/15 text-amber-300 border-amber-500/30' 
                              : (isStructuring ? 'bg-purple-500/15 text-purple-300 border-purple-500/30' : 'bg-slate-800 text-slate-300 border-slate-700'))
                      }`}>
                        {item.pattern_type}
                      </span>
                      <span className="text-xs font-mono text-slate-400">
                        {item.members?.length || 0} entities
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-white mb-1.5 mono">
                      {item.typology_id}
                    </h3>

                    <p className="text-xs text-slate-300 leading-relaxed mb-3">
                      {item.narrative}
                    </p>

                    {item.honesty_notes && (
                      <div className="p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 text-[11px] text-slate-400">
                        <strong className="text-sky-300 block mb-0.5">Scientific Evaluation:</strong>
                        {item.honesty_notes}
                      </div>
                    )}
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs font-semibold text-sky-400">
                    <span>Inspect {item.edges?.length || 0} Evidence Edges</span>
                    <ChevronRight className="w-4 h-4" />
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* OddBall Structural Anomaly View */}
        {activeTab === 'oddball' && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300 flex items-start justify-between">
              <div>
                <h3 className="text-sm font-bold text-white mb-1">
                  OddBall Structural Power-Law Anomaly Detection (Akoglu et al.)
                </h3>
                <p className="max-w-3xl leading-relaxed text-slate-400">
                  Fits power law <em>edges ≈ C · nodes^α</em> on egonets. Deviations below expectation identify <strong>STAR hubs (mule-like)</strong>; deviations above identify <strong>NEAR-CLIQUES (fraud cells)</strong>. 
                  Unsupervised achievement: Scatter source <strong className="text-amber-400 font-bold">A00055</strong> surfaced at <strong className="text-emerald-400 font-bold">rank 6/532 (top 1.1%)</strong> without pre-labeled rules!
                </p>
              </div>
              <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300 text-right mono shrink-0">
                <div className="text-lg font-black">A00055</div>
                <div className="text-[10px]">Rank 6 / Top 1.1%</div>
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-900/40">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/90 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="p-3">Rank</th>
                    <th className="p-3">Account ID</th>
                    <th className="p-3">Shape-Norm Score</th>
                    <th className="p-3">Raw Score</th>
                    <th className="p-3">Egonet Topology</th>
                    <th className="p-3">Egonet Edges vs Expected</th>
                    <th className="p-3">Account Holder</th>
                    <th className="p-3">Bank</th>
                    <th className="p-3">Intelligence Flag</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                  {oddballList?.map((row) => (
                    <tr 
                      key={row.account_id}
                      className={`hover:bg-slate-800/40 transition-colors ${
                        row.account_id === 'A00055' ? 'bg-amber-500/10 font-bold' : ''
                      }`}
                    >
                      <td className="p-3 text-slate-400">#{row.rank}</td>
                      <td className="p-3 text-sky-400 font-bold">{row.account_id}</td>
                      <td className="p-3 text-amber-400">{row.score}</td>
                      <td className="p-3 text-slate-400">{row.raw_score}</td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          row.ego_shape === 'STAR' ? 'bg-blue-500/20 text-blue-300' : 'bg-purple-500/20 text-purple-300'
                        }`}>
                          {row.ego_shape}
                        </span>
                      </td>
                      <td className="p-3 text-slate-300">{row.egonet_edges} / {row.expected_edges}</td>
                      <td className="p-3 font-sans text-white">{row.holder_name}</td>
                      <td className="p-3 font-sans text-slate-400">{row.bank}</td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          row.flag === 'DISCOVERED_SCATTER'
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                            : 'bg-slate-800 text-slate-400'
                        }`}>
                          {row.flag}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 48h Temporal Burst Anomaly View */}
        {activeTab === 'temporal' && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300 flex items-start justify-between">
              <div>
                <h3 className="text-sm font-bold text-white mb-1">
                  48-Hour Temporal Sliding Window & Z-Score Composite (Tier 2b)
                </h3>
                <p className="max-w-3xl leading-relaxed text-slate-400">
                  Calculates interval regularity, transaction frequency, and amount variance across a 48h sliding burst window. 
                  Direct scientific win: While Louvain fragmented the 6 structuring accounts (<strong className="text-white">A00069–A00074</strong>) across 6 different communities, this detector unified all 6 accounts together at <strong className="text-purple-400 font-bold">ranks 1 through 6</strong>!
                </p>
              </div>
              <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/30 text-purple-300 text-right mono shrink-0">
                <div className="text-lg font-black">A00069–74</div>
                <div className="text-[10px]">Ranks 1–6 (100% Purity)</div>
              </div>
            </div>

            <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-900/40">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/90 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
                  <tr>
                    <th className="p-3">Rank</th>
                    <th className="p-3">Account ID</th>
                    <th className="p-3">Temporal Composite Score</th>
                    <th className="p-3">Burst Ratio</th>
                    <th className="p-3">Burst Tx Count</th>
                    <th className="p-3">Mean Interval Gap</th>
                    <th className="p-3">Mean Amount</th>
                    <th className="p-3">Holder Name</th>
                    <th className="p-3">Bank</th>
                    <th className="p-3">Smurfing Flag</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                  {temporalList?.map((row) => (
                    <tr 
                      key={row.account_id}
                      className={`hover:bg-slate-800/40 transition-colors ${
                        row.flag === 'SMURFING_RING' ? 'bg-purple-500/10 font-bold' : ''
                      }`}
                    >
                      <td className="p-3 text-slate-400">#{row.rank}</td>
                      <td className="p-3 text-sky-400 font-bold">{row.account_id}</td>
                      <td className="p-3 text-purple-400 font-bold">{row.temporal_score}</td>
                      <td className="p-3 text-slate-300">{row.burst_ratio}</td>
                      <td className="p-3 text-slate-300">{row.burst_tx_count} txs</td>
                      <td className="p-3 text-slate-300">{row.mean_gap_min} min</td>
                      <td className="p-3 text-emerald-400">{formatINR(row.mean_amount)}</td>
                      <td className="p-3 font-sans text-white">{row.holder_name}</td>
                      <td className="p-3 font-sans text-slate-400">{row.bank}</td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          row.flag === 'SMURFING_RING'
                            ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40'
                            : 'bg-slate-800 text-slate-400'
                        }`}>
                          {row.flag}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
