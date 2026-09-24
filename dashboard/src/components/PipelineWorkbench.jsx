import React, { useState, useEffect } from 'react';
import { 
  Play, 
  CheckCircle2, 
  AlertTriangle, 
  ShieldAlert, 
  Workflow, 
  Database, 
  Cpu, 
  FileText, 
  ArrowRight, 
  Lock, 
  Sparkles, 
  Layers, 
  RefreshCw,
  Search,
  ExternalLink,
  ChevronRight,
  TrendingUp,
  FileCheck2,
  Clock,
  Fingerprint
} from 'lucide-react';
import pipelineData from '../data/pipeline_data.json';

export default function PipelineWorkbench({ 
  onInspectLeadSubgraph, 
  onOpenBSACertificate 
}) {
  const [selectedSampleKey, setSelectedSampleKey] = useState('fir');
  const [customText, setCustomText] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [activeStageIndex, setActiveStageIndex] = useState(5); // Default to completed view
  const [pipelineResult, setPipelineResult] = useState(null);
  const [selectedLeadIndex, setSelectedLeadIndex] = useState(0);

  // Initialize with precomputed run for the default sample
  useEffect(() => {
    if (pipelineData?.precomputed_runs?.[selectedSampleKey]) {
      setPipelineResult(pipelineData.precomputed_runs[selectedSampleKey]);
      setSelectedLeadIndex(0);
    }
  }, [selectedSampleKey]);

  // Execute Pipeline with live step animation
  const handleExecutePipeline = () => {
    setIsRunning(true);
    setActiveStageIndex(0);

    const stepInterval = 400; // ms per stage
    let currentStep = 0;

    const timer = setInterval(() => {
      currentStep += 1;
      if (currentStep <= 5) {
        setActiveStageIndex(currentStep);
      } else {
        clearInterval(timer);
        setIsRunning(false);
        // Load the run results
        const runData = pipelineData?.precomputed_runs?.[selectedSampleKey];
        if (runData) {
          setPipelineResult(runData);
        }
      }
    }, stepInterval);
  };

  const samplePresets = [
    {
      key: 'fir',
      name: 'Cyber Fraud FIR (Mule Hub)',
      tag: 'Unstructured Text',
      desc: 'FIR narrative referencing suspect Rahul Joshi (राहुल जोशी / P00231), collector A00013, and 12 feeder accounts.',
      badge: 'Tier 1 & OddBall',
      badgeColor: 'border-red-500/30 text-red-400 bg-red-500/10'
    },
    {
      key: 'structuring',
      name: 'Bank Transaction Stream',
      tag: 'Structured Feed',
      desc: 'Batch of 6 transactions tightly clustered at ₹9,200 - ₹9,900 to evade ₹50,000 PMLA reporting threshold.',
      badge: 'Structuring / Smurfing',
      badgeColor: 'border-amber-500/30 text-amber-400 bg-amber-500/10'
    },
    {
      key: 'cdr',
      name: 'CDR Telecommunications Log',
      tag: 'Telecom Feed',
      desc: 'High-frequency coordination burst between suspect phone PH04296 and accomplices within 48h window.',
      badge: 'Temporal Burst Z=3.8',
      badgeColor: 'border-purple-500/30 text-purple-400 bg-purple-500/10'
    },
    {
      key: 'scatter',
      name: 'Scatter-Gather Transaction Flow',
      tag: 'Layering Stream',
      desc: 'Rapid dispersion from source A00055 through 4 layering conduits, reconverging into aggregator A00064.',
      badge: 'Scatter-Gather',
      badgeColor: 'border-blue-500/30 text-blue-400 bg-blue-500/10'
    }
  ];

  const currentSample = pipelineData?.samples?.[selectedSampleKey];
  const activeLead = pipelineResult?.leads?.[selectedLeadIndex] || pipelineResult?.leads?.[0];

  const stages = [
    { id: 1, name: 'Raw Input Ingestion', icon: FileText, desc: 'Extracts tokens, amounts, entities' },
    { id: 2, name: 'Multilingual Resolution', icon: RefreshCw, desc: 'Devanagari, initials & OCR repair' },
    { id: 3, name: 'Graph Tri-Partite Ingestion', icon: Database, desc: 'Classifies Explicit / Inferred / Predicted' },
    { id: 4, name: 'Multi-Tier Anomaly Engine', icon: Cpu, desc: 'Typologies, OddBall, Bursts, Link Prediction' },
    { id: 5, name: 'Court-Admissible Leads', icon: FileCheck2, desc: 'Section 63 BSA certified dossiers' }
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner: Core Mission Statement */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950/70 to-slate-900 border border-indigo-500/20 p-6 shadow-xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 flex items-center gap-1.5">
                <Workflow className="w-3 h-3" /> Core System Architecture · SIH PS 189
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                Section 63 BSA Compliant
              </span>
            </div>
            <h2 className="text-2xl font-bold text-slate-100 tracking-tight flex items-center gap-2">
              End-to-End Input-to-Leads Investigative Pipeline
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-3xl leading-relaxed">
              Automated transformation pipeline taking raw, noisy, multilingual multi-source intelligence
              (FIR complaints, bank feeds, CDR streams) and running it through entity resolution, 
              knowledge graph ingestion with tri-partite taxonomy, and multi-tier anomaly detection to synthesize 
              court-admissible investigative leads.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleExecutePipeline}
              disabled={isRunning}
              className={`flex items-center gap-2.5 px-6 py-3 rounded-xl font-bold text-xs uppercase tracking-wider shadow-lg transition-all transform hover:-translate-y-0.5 ${
                isRunning 
                  ? 'bg-slate-700 text-slate-400 cursor-not-allowed' 
                  : 'bg-gradient-to-r from-indigo-500 via-sky-500 to-emerald-500 hover:from-indigo-600 hover:to-emerald-600 text-white shadow-indigo-500/25'
              }`}
            >
              {isRunning ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-white" />
                  <span>Executing Pipeline ({activeStageIndex}/5)...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current text-white" />
                  <span>Execute Full Pipeline</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* 5-Stage Visual Stepper */}
        <div className="mt-6 pt-5 border-t border-slate-800/80">
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {stages.map((stage) => {
              const Icon = stage.icon;
              const isPast = activeStageIndex >= stage.id;
              const isCurrent = activeStageIndex === stage.id && isRunning;
              return (
                <div 
                  key={stage.id}
                  onClick={() => !isRunning && setActiveStageIndex(stage.id)}
                  className={`cursor-pointer rounded-xl p-3 border transition-all ${
                    isCurrent 
                      ? 'bg-indigo-500/20 border-indigo-400 shadow-md shadow-indigo-500/20 ring-1 ring-indigo-400' 
                      : isPast
                        ? 'bg-slate-800/70 border-emerald-500/30'
                        : 'bg-slate-900/40 border-slate-800 opacity-60'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-mono text-slate-400">STAGE {stage.id}</span>
                    {isCurrent ? (
                      <RefreshCw className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
                    ) : isPast ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <div className="w-2 h-2 rounded-full bg-slate-700" />
                    )}
                  </div>
                  <div className="flex items-center gap-1.5 font-semibold text-xs text-slate-200">
                    <Icon className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                    <span className="truncate">{stage.name}</span>
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1 line-clamp-1">{stage.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Grid: Sample Selector & Input Preview (Left) vs Pipeline Output & Leads (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: Input Preset Selector & Raw Ingestion */}
        <div className="lg:col-span-4 space-y-4">
          <div className="rounded-xl bg-[#0e1626] border border-slate-800 p-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2 mb-3">
              <Database className="w-4 h-4 text-indigo-400" />
              <span>Select Sample Input Feed</span>
            </h3>

            <div className="space-y-2.5">
              {samplePresets.map((preset) => {
                const isSelected = selectedSampleKey === preset.key;
                return (
                  <button
                    key={preset.key}
                    onClick={() => {
                      setSelectedSampleKey(preset.key);
                      setActiveStageIndex(5);
                    }}
                    className={`w-full text-left p-3 rounded-lg border transition-all ${
                      isSelected
                        ? 'bg-indigo-950/40 border-indigo-500 shadow-sm shadow-indigo-500/10'
                        : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-slate-200">{preset.name}</span>
                      <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded border ${preset.badgeColor}`}>
                        {preset.badge}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                      {preset.desc}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Raw Input Content Viewer */}
          <div className="rounded-xl bg-[#0e1626] border border-slate-800 p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-sky-400" /> Raw Ingestion Payload
              </span>
              <span className="text-[10px] font-mono text-slate-400">
                {currentSample?.source_type}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-300 max-h-64 overflow-y-auto leading-relaxed">
              {currentSample?.raw_text ? (
                <pre className="whitespace-pre-wrap">{currentSample.raw_text.trim()}</pre>
              ) : (
                <pre className="whitespace-pre-wrap">{JSON.stringify(currentSample?.records || currentSample, null, 2)}</pre>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Execution Results & Lead Dossiers */}
        <div className="lg:col-span-8 space-y-4">
          
          {/* Stage Details Tabs / Status Counters */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="rounded-xl bg-[#0e1626] border border-slate-800 p-3">
              <span className="text-[10px] uppercase font-mono text-slate-400">Extracted Entities</span>
              <div className="text-lg font-bold text-sky-400 mt-0.5">
                {(pipelineResult?.extracted_entities?.accounts?.length || 0) + 
                 (pipelineResult?.extracted_entities?.phones?.length || 0) + 
                 (pipelineResult?.extracted_entities?.persons?.length || 0)}
              </div>
              <span className="text-[10px] text-slate-500">
                {pipelineResult?.extracted_entities?.accounts?.length || 0} Accounts · {pipelineResult?.extracted_entities?.persons?.length || 0} Persons
              </span>
            </div>

            <div className="rounded-xl bg-[#0e1626] border border-slate-800 p-3">
              <span className="text-[10px] uppercase font-mono text-slate-400">Resolved Aliases</span>
              <div className="text-lg font-bold text-emerald-400 mt-0.5">
                {pipelineResult?.resolved_entities?.length || 0}
              </div>
              <span className="text-[10px] text-slate-500">
                Devanagari & Initials Stitched
              </span>
            </div>

            <div className="rounded-xl bg-[#0e1626] border border-slate-800 p-3">
              <span className="text-[10px] uppercase font-mono text-slate-400">Graph Tri-Partite Edges</span>
              <div className="text-lg font-bold text-indigo-400 mt-0.5">
                {pipelineResult?.graph_state?.summary?.total_edges || 0}
              </div>
              <span className="text-[10px] text-slate-500">
                Explicit: {pipelineResult?.graph_state?.summary?.taxonomy_breakdown?.Explicit || 0} · Inferred: {pipelineResult?.graph_state?.summary?.taxonomy_breakdown?.Inferred || 0}
              </span>
            </div>

            <div className="rounded-xl bg-[#0e1626] border border-slate-800 p-3">
              <span className="text-[10px] uppercase font-mono text-slate-400">Generated Leads</span>
              <div className="text-lg font-bold text-amber-400 mt-0.5">
                {pipelineResult?.leads?.length || 0}
              </div>
              <span className="text-[10px] text-slate-500">
                Section 63 BSA Certified
              </span>
            </div>
          </div>

          {/* Multilingual Entity Resolution Showcase Bar */}
          {pipelineResult?.resolved_entities && pipelineResult.resolved_entities.length > 0 && (
            <div className="rounded-xl bg-slate-900/60 border border-slate-800 p-3 flex flex-wrap items-center gap-2">
              <span className="text-xs font-bold text-slate-400 flex items-center gap-1 mr-2">
                <RefreshCw className="w-3 h-3 text-emerald-400" /> Resolution Links:
              </span>
              {pipelineResult.resolved_entities.map((rp, idx) => (
                <div 
                  key={idx}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700 text-xs"
                >
                  <span className="font-hindi text-amber-300 font-medium">{rp.raw_mention}</span>
                  <ArrowRight className="w-3 h-3 text-slate-500" />
                  <span className="font-semibold text-emerald-400">{rp.canonical_name}</span>
                  <span className="text-[10px] font-mono text-slate-400">({rp.canonical_id})</span>
                  <span className="text-[9px] px-1 rounded bg-slate-700 text-slate-300">
                    {Math.round(rp.confidence * 100)}%
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Leads Carousel / List */}
          <div className="rounded-xl bg-[#0e1626] border border-slate-800 p-5 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-amber-400" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                  Prioritized Investigative Leads ({pipelineResult?.leads?.length || 0})
                </h3>
              </div>
              
              <div className="flex items-center gap-1.5">
                {pipelineResult?.leads?.map((lead, idx) => (
                  <button
                    key={lead.lead_id}
                    onClick={() => setSelectedLeadIndex(idx)}
                    className={`px-2.5 py-1 rounded text-xs font-mono font-semibold transition-all ${
                      selectedLeadIndex === idx
                        ? 'bg-amber-500 text-slate-950 shadow-md shadow-amber-500/20'
                        : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                    }`}
                  >
                    #{idx + 1}
                  </button>
                ))}
              </div>
            </div>

            {/* Active Lead Inspection Card */}
            {activeLead ? (
              <div className="rounded-xl border border-slate-700/80 bg-slate-900/90 p-5 space-y-5">
                {/* Lead Header */}
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-3 border-b border-slate-800 pb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                        activeLead.threat_level === 'CRITICAL'
                          ? 'bg-red-500/20 text-red-400 border border-red-500/40'
                          : activeLead.threat_level === 'HIGH'
                            ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                            : 'bg-sky-500/20 text-sky-400 border border-sky-500/40'
                      }`}>
                        {activeLead.threat_level} Priority
                      </span>
                      <span className="text-[11px] font-mono text-slate-400">
                        {activeLead.lead_id}
                      </span>
                      <span className="text-[10px] text-slate-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" /> {activeLead.generated_at}
                      </span>
                    </div>
                    <h4 className="text-base font-bold text-slate-100">
                      {activeLead.title}
                    </h4>
                  </div>

                  {/* Quick Action Buttons */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onInspectLeadSubgraph && onInspectLeadSubgraph(activeLead)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-sky-600/20 hover:bg-sky-600/30 text-sky-400 border border-sky-500/30 text-xs font-semibold transition-all"
                      title="Load this lead's evidence subgraph into D3 interactive graph"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      <span>Inspect in Graph Studio</span>
                    </button>

                    <button
                      onClick={() => onOpenBSACertificate && onOpenBSACertificate(activeLead)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-md shadow-emerald-600/20 transition-all"
                      title="Generate court-ready Section 63 BSA certificate"
                    >
                      <FileCheck2 className="w-3.5 h-3.5" />
                      <span>Export BSA Certificate</span>
                    </button>
                  </div>
                </div>

                {/* Evidentiary Narrative */}
                <div>
                  <h5 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                    Evidentiary Narrative & Analytical Rationale
                  </h5>
                  <p className="text-xs text-slate-200 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                    {activeLead.narrative_summary}
                  </p>
                </div>

                {/* Target Suspect & Evidence Subgraph Details */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-2">
                    <h5 className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                      <Search className="w-3 h-3 text-sky-400" /> Primary Identified Suspect
                    </h5>
                    <div className="space-y-1">
                      <div className="text-xs font-bold text-slate-100 flex items-center gap-2">
                        <span>{activeLead.primary_suspect?.canonical_name || 'Unidentified'}</span>
                        <span className="text-[10px] font-mono text-slate-400">
                          ({activeLead.primary_suspect?.canonical_id})
                        </span>
                      </div>
                      {activeLead.primary_suspect?.resolved_aliases?.length > 0 && (
                        <div className="text-[11px] text-amber-300">
                          Aliases: {activeLead.primary_suspect.resolved_aliases.join(', ')}
                        </div>
                      )}
                      <div className="text-[10px] text-slate-400">
                        Resolution Confidence: {Math.round((activeLead.primary_suspect?.match_confidence || 0.8) * 100)}%
                      </div>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/80 space-y-2">
                    <h5 className="text-[10px] font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                      <Layers className="w-3 h-3 text-indigo-400" /> Evidence Subgraph Composition
                    </h5>
                    <div className="text-xs text-slate-300 space-y-1">
                      <div>
                        Nodes Flagged: <strong className="text-indigo-400">{activeLead.evidence_subgraph?.nodes?.length || 0}</strong> entities
                      </div>
                      <div>
                        Edges Linked: <strong className="text-indigo-400">{activeLead.evidence_subgraph?.edges?.length || 0}</strong> transactions / events
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono">
                        Classification: Explicit / Tri-Partite
                      </div>
                    </div>
                  </div>
                </div>

                {/* Statutory Actionable Recommendations (CrPC) */}
                <div>
                  <h5 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                    Actionable Statutory Next Steps (Human Investigator Review)
                  </h5>
                  <div className="space-y-1.5">
                    {activeLead.actionable_recommendations?.map((rec, rIdx) => (
                      <div 
                        key={rIdx}
                        className="flex items-start gap-2 text-xs text-slate-200 bg-amber-500/5 border border-amber-500/20 p-2.5 rounded-lg"
                      >
                        <span className="text-amber-400 font-bold mt-0.5">•</span>
                        <span>{rec}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Section 63 BSA Digital Custody Seal */}
                <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-slate-800 text-[11px] text-slate-400">
                  <div className="flex items-center gap-2">
                    <Fingerprint className="w-4 h-4 text-emerald-400" />
                    <span>Section 63 BSA SHA-256 Custody Hash:</span>
                    <span className="font-mono text-emerald-400 font-medium">
                      {activeLead.section_63_bsa_custody_hash || activeLead.custody_hash}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-500 uppercase tracking-wider">
                    Tamper-Evident Forensic Record
                  </span>
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-slate-500">
                Click "Execute Full Pipeline" to generate and inspect court-admissible leads.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
