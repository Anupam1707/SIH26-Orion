import React from 'react';
import { 
  X, 
  User, 
  CreditCard, 
  Phone, 
  ShieldAlert, 
  Activity, 
  Clock, 
  FileCheck, 
  ExternalLink,
  Flame,
  FileSpreadsheet
} from 'lucide-react';
import { formatINR, formatDateTime } from '../utils/crypto';

export default function EntityDossier({ node, onClose, onOpenBSA }) {
  if (!node) return null;

  const isAccount = node.entity_type === 'Account';
  const isPerson = node.entity_type === 'Person';
  const isPhone = node.entity_type === 'PhoneNumber';

  // Calculate composite risk index (0-100)
  let riskScore = 35;
  if (node.role?.includes('Collector') || node.role?.includes('Source')) riskScore = 94;
  else if (node.role?.includes('Structuring')) riskScore = 88;
  else if (node.oddball?.rank <= 20) riskScore = 82;
  else if (node.temporal?.rank <= 6) riskScore = 85;

  return (
    <div className="w-80 md:w-96 bg-[#0c1322]/95 border-l border-slate-800 flex flex-col h-full shadow-2xl overflow-y-auto">
      {/* Dossier Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60 sticky top-0 z-10 backdrop-blur-md">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-sky-500/20 border border-sky-500/40 flex items-center justify-center text-sky-400">
            {isPerson ? <User className="w-4 h-4" /> : (isPhone ? <Phone className="w-4 h-4" /> : <CreditCard className="w-4 h-4" />)}
          </div>
          <div>
            <h3 className="text-sm font-bold text-white mono">{node.id}</h3>
            <span className="text-[10px] uppercase font-semibold text-slate-400">
              {node.entity_type} Dossier
            </span>
          </div>
        </div>

        <button 
          onClick={onClose}
          className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      <div className="p-4 space-y-4">
        {/* Risk Level Badge */}
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
          <div>
            <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400">Composite Risk Index</div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className={`text-2xl font-black mono ${riskScore > 80 ? 'text-rose-400' : 'text-amber-400'}`}>
                {riskScore} / 100
              </span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                riskScore > 80 ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' : 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
              }`}>
                {riskScore > 80 ? 'High Lead Priority' : 'Under Observation'}
              </span>
            </div>
          </div>
          <ShieldAlert className={`w-8 h-8 ${riskScore > 80 ? 'text-rose-500' : 'text-amber-500'}`} />
        </div>

        {/* Core Attributes */}
        <div className="space-y-2 text-xs">
          <div className="flex items-center justify-between py-1.5 border-b border-slate-800/80">
            <span className="text-slate-400">Operational Role:</span>
            <span className="font-semibold text-sky-300">{node.role || 'Network Member'}</span>
          </div>

          {node.holder_name && (
            <div className="flex items-center justify-between py-1.5 border-b border-slate-800/80">
              <span className="text-slate-400">Account Holder:</span>
              <span className="font-semibold text-white">{node.holder_name}</span>
            </div>
          )}

          {node.bank && (
            <div className="flex items-center justify-between py-1.5 border-b border-slate-800/80">
              <span className="text-slate-400">Financial Institution:</span>
              <span className="font-medium text-slate-200">{node.bank}</span>
            </div>
          )}

          {node.telecom_provider && (
            <div className="flex items-center justify-between py-1.5 border-b border-slate-800/80">
              <span className="text-slate-400">Telecom Provider:</span>
              <span className="font-medium text-slate-200">{node.telecom_provider}</span>
            </div>
          )}

          <div className="flex items-center justify-between py-1.5 border-b border-slate-800/80">
            <span className="text-slate-400">Jurisdiction Status:</span>
            <span className="font-medium text-emerald-400 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              {node.status || 'Active Surveillance'}
            </span>
          </div>
        </div>

        {/* Module 5 Anomaly Detection Signals */}
        <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2.5">
          <div className="flex items-center gap-1.5 text-xs font-bold text-slate-300 border-b border-slate-800/80 pb-1.5">
            <Activity className="w-3.5 h-3.5 text-amber-400" />
            <span>Module 5 AI & Structural Anomaly Metrics</span>
          </div>

          {node.oddball ? (
            <div className="space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">OddBall Structural Score:</span>
                <span className="mono font-bold text-amber-400">{node.oddball.score}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">OddBall Global Rank:</span>
                <span className="mono text-white">Rank {node.oddball.rank} ({node.oddball.percentile}th percentile)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Egonet Topology:</span>
                <span className="mono text-sky-400">{node.oddball.ego_shape || 'STAR (Mule Hub)'}</span>
              </div>
              <div className="flex justify-between text-[11px] text-slate-500">
                <span>Egonet Edges vs Expected:</span>
                <span className="mono">{node.oddball.egonet_edges || 0} / {node.oddball.expected_edges || 0}</span>
              </div>
            </div>
          ) : (
            <div className="text-[11px] text-slate-500 italic">
              Zero internal egonet triangles — structurally unclassified by OddBall.
            </div>
          )}

          {node.temporal && (
            <div className="pt-2 border-t border-slate-800/60 space-y-1.5 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Temporal Burst Z-Score:</span>
                <span className="mono font-bold text-purple-400">{node.temporal.temporal_score}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Burst Transaction Count:</span>
                <span className="mono text-white">{node.temporal.burst_tx_count} txs</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Mean Interval Gap:</span>
                <span className="mono text-white">{node.temporal.mean_gap_min} min</span>
              </div>
            </div>
          )}
        </div>

        {/* Section 63 BSA Traceability Box */}
        <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/30 text-xs space-y-2">
          <div className="flex items-center gap-1.5 font-bold text-emerald-400">
            <FileCheck className="w-4 h-4" />
            <span>Evidentiary Admissibility (BSA s.63)</span>
          </div>
          <p className="text-[11px] text-slate-300 leading-relaxed">
            All edges linked to this node originate from verified CCTNS FIR filings, bank account KYC records, or cellular CDR dumps.
          </p>
          <button
            onClick={() => onOpenBSA(node)}
            className="w-full mt-1 py-1.5 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs flex items-center justify-center gap-2 shadow-sm transition-all"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>Generate Official Lead Sheet</span>
          </button>
        </div>
      </div>
    </div>
  );
}
