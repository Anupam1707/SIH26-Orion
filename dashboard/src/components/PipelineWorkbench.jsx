import React, { useState, useEffect } from 'react';
import { 
  Play, 
  CheckCircle2, 
  AlertTriangle, 
  Shield, 
  Database, 
  FileText, 
  ArrowRight, 
  RefreshCw,
  Search,
  ExternalLink,
  Clock,
  Fingerprint,
  Layers,
  ChevronRight,
  Printer
} from 'lucide-react';
import pipelineData from '../data/pipeline_data.json';

export default function PipelineWorkbench({ 
  onInspectLeadSubgraph, 
  onOpenBSACertificate 
}) {
  const [selectedSampleKey, setSelectedSampleKey] = useState('fir');
  const [customText, setCustomText] = useState('');
  const [isCustomMode, setIsCustomMode] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [activeStageIndex, setActiveStageIndex] = useState(5);
  const [pipelineResult, setPipelineResult] = useState(null);
  const [selectedLeadIndex, setSelectedLeadIndex] = useState(0);

  // Initialize with precomputed run for the selected sample
  useEffect(() => {
    if (!isCustomMode && pipelineData?.precomputed_runs?.[selectedSampleKey]) {
      setPipelineResult(pipelineData.precomputed_runs[selectedSampleKey]);
      setSelectedLeadIndex(0);
    }
  }, [selectedSampleKey, isCustomMode]);

  // Execute Pipeline with step progression
  const handleExecutePipeline = () => {
    setIsRunning(true);
    setActiveStageIndex(0);

    const stepInterval = 300;
    let currentStep = 0;

    const timer = setInterval(() => {
      currentStep += 1;
      if (currentStep <= 5) {
        setActiveStageIndex(currentStep);
      } else {
        clearInterval(timer);
        setIsRunning(false);
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
      name: 'FIR: Cyber Mule Network',
      type: 'Unstructured Police FIR',
      desc: 'Case complaint in English with Devanagari suspect name (राहुल जोशी / P00231), 12 feeder accounts, and collector A00013.',
      badge: 'Mule Fan-In'
    },
    {
      key: 'structuring',
      name: 'Bank Transaction Stream',
      type: 'Financial CSV Stream',
      desc: 'Batch of 6 transfers under ₹10,000 threshold across accounts A00069-A00074 to avoid regulatory CTR reporting.',
      badge: 'Structuring'
    },
    {
      key: 'cdr',
      name: 'CDR Call Detail Records',
      type: 'Telecommunications Feed',
      desc: 'Pre-incident 48-hour call frequency burst between suspect mobile PH04296 and coordination ring.',
      badge: 'Call Burst'
    },
    {
      key: 'scatter',
      name: 'Scatter-Gather Flow',
      type: 'Layering Stream',
      desc: 'Single source A00055 rapidly dispersing ₹60,000 across 4 intermediary accounts, reconverging at A00064.',
      badge: 'Layering'
    }
  ];

  const currentSample = pipelineData?.samples?.[selectedSampleKey];
  const activeLead = pipelineResult?.leads?.[selectedLeadIndex] || pipelineResult?.leads?.[0];

  const stages = [
    { id: 1, name: '1. Ingestion', desc: 'Parse tokens & records' },
    { id: 2, name: '2. Resolution', desc: 'Stitch aliases & KYC' },
    { id: 3, name: '3. Graph Update', desc: 'Tag explicit/inferred edges' },
    { id: 4, name: '4. Detection', desc: 'Rules, OddBall, bursts' },
    { id: 5, name: '5. Lead Output', desc: 'Section 63 BSA dossiers' }
  ];

  return (
    <div className="space-y-4 max-w-7xl mx-auto pb-10">
      {/* Control Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono">
                Pipeline Control
              </span>
              <span className="text-slate-600">•</span>
              <span className="text-xs text-slate-400">
                Automated Input-to-Leads Processing
              </span>
            </div>
            <h2 className="text-base font-bold text-slate-100">
              Evidence Ingestion & Investigative Lead Synthesis
            </h2>
          </div>

          <div className="flex items-center gap-2.5">
            <button
              onClick={handleExecutePipeline}
              disabled={isRunning}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-xs font-semibold transition-colors ${
                isRunning
                  ? 'bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700'
                  : 'bg-blue-600 hover:bg-blue-500 text-white'
              }`}
            >
              {isRunning ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Processing Stage {activeStageIndex}/5...</span>
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5 fill-current" />
                  <span>Run Pipeline</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Linear Stepper */}
        <div className="mt-4 pt-3 border-t border-slate-800 grid grid-cols-2 md:grid-cols-5 gap-2">
          {stages.map((st) => {
            const isDone = activeStageIndex >= st.id;
            const isCurrent = activeStageIndex === st.id && isRunning;
            return (
              <div 
                key={st.id}
                onClick={() => !isRunning && setActiveStageIndex(st.id)}
                className={`p-2.5 rounded border transition-colors cursor-pointer text-left ${
                  isCurrent
                    ? 'bg-blue-950/40 border-blue-500/80'
                    : isDone
                      ? 'bg-slate-800/60 border-slate-700 text-slate-200'
                      : 'bg-slate-900/40 border-slate-800 text-slate-500'
                }`}
              >
                <div className="flex items-center justify-between text-[11px] font-semibold mb-0.5">
                  <span className={isDone ? 'text-slate-200' : 'text-slate-500'}>{st.name}</span>
                  {isDone ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-blue-400" />
                  ) : (
                    <div className="w-1.5 h-1.5 rounded-full bg-slate-700" />
                  )}
                </div>
                <div className="text-[10px] text-slate-400 truncate">{st.desc}</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Grid: Input Column & Output Column */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        
        {/* Left Column: Input Feed & Preview */}
        <div className="lg:col-span-4 space-y-4">
          
          {/* Sample Preset Selector */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-3.5 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-slate-400" /> Input Feed Source
              </span>
              <span className="text-[10px] font-mono text-slate-500">4 Presets</span>
            </div>

            <div className="space-y-1.5">
              {samplePresets.map((preset) => {
                const isSelected = selectedSampleKey === preset.key && !isCustomMode;
                return (
                  <button
                    key={preset.key}
                    onClick={() => {
                      setIsCustomMode(false);
                      setSelectedSampleKey(preset.key);
                      setActiveStageIndex(5);
                    }}
                    className={`w-full text-left p-2.5 rounded border transition-colors ${
                      isSelected
                        ? 'bg-slate-800 border-blue-500/80 text-slate-100'
                        : 'bg-slate-950/60 border-slate-800/80 text-slate-300 hover:bg-slate-800/50 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold">{preset.name}</span>
                      <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 border border-slate-700">
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

          {/* Raw Payload Inspector */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-3.5 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-slate-400" /> Ingestion Text / Data
              </span>
              <span className="text-[10px] font-mono text-slate-500">
                {currentSample?.source_type}
              </span>
            </div>

            <div className="bg-slate-950 border border-slate-800 rounded p-2.5 font-mono text-[11px] text-slate-300 max-h-56 overflow-y-auto leading-relaxed whitespace-pre-wrap select-text">
              {currentSample?.raw_text ? currentSample.raw_text.trim() : JSON.stringify(currentSample?.records || currentSample, null, 2)}
            </div>
          </div>
        </div>

        {/* Right Column: Pipeline Execution & Generated Leads */}
        <div className="lg:col-span-8 space-y-4">
          
          {/* Key Pipeline Stats Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-3">
              <div className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">Extracted Entities</div>
              <div className="text-base font-bold text-slate-100 font-mono mt-0.5">
                {(pipelineResult?.extracted_entities?.accounts?.length || 0) + 
                 (pipelineResult?.extracted_entities?.phones?.length || 0) + 
                 (pipelineResult?.extracted_entities?.persons?.length || 0)}
              </div>
              <div className="text-[10px] text-slate-500 truncate mt-0.5">
                {pipelineResult?.extracted_entities?.accounts?.length || 0} Accounts · {pipelineResult?.extracted_entities?.persons?.length || 0} Persons
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-lg p-3">
              <div className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">Resolved Aliases</div>
              <div className="text-base font-bold text-slate-100 font-mono mt-0.5">
                {pipelineResult?.resolved_entities?.length || 0}
              </div>
              <div className="text-[10px] text-slate-500 truncate mt-0.5">
                Devanagari & Initials
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-lg p-3">
              <div className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">Graph Edges Added</div>
              <div className="text-base font-bold text-slate-100 font-mono mt-0.5">
                {pipelineResult?.graph_state?.summary?.total_edges || 0}
              </div>
              <div className="text-[10px] text-slate-500 truncate mt-0.5">
                Explicit: {pipelineResult?.graph_state?.summary?.taxonomy_breakdown?.Explicit || 0}
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-lg p-3">
              <div className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">Generated Leads</div>
              <div className="text-base font-bold text-amber-400 font-mono mt-0.5">
                {pipelineResult?.leads?.length || 0}
              </div>
              <div className="text-[10px] text-slate-500 truncate mt-0.5">
                Section 63 BSA Certified
              </div>
            </div>
          </div>

          {/* Multilingual Match Indicator Bar */}
          {pipelineResult?.resolved_entities && pipelineResult.resolved_entities.length > 0 && (
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-3">
              <div className="text-xs font-semibold text-slate-400 mb-2 flex items-center gap-1.5">
                <span>Resolved Entity Mapping (Cross-Lingual)</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {pipelineResult.resolved_entities.map((rp, idx) => (
                  <div 
                    key={idx}
                    className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-950 border border-slate-800 text-xs font-mono"
                  >
                    <span className="text-amber-300 font-sans font-medium">{rp.raw_mention}</span>
                    <ArrowRight className="w-3 h-3 text-slate-600" />
                    <span className="text-slate-100 font-sans font-medium">{rp.canonical_name}</span>
                    <span className="text-[10px] text-slate-400">({rp.canonical_id})</span>
                    <span className="text-[10px] px-1 rounded bg-slate-800 text-slate-300">
                      {Math.round(rp.confidence * 100)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Leads Section */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
                  Actionable Investigative Leads ({pipelineResult?.leads?.length || 0})
                </span>
              </div>

              <div className="flex items-center gap-1">
                {pipelineResult?.leads?.map((lead, idx) => (
                  <button
                    key={lead.lead_id}
                    onClick={() => setSelectedLeadIndex(idx)}
                    className={`px-2 py-0.5 rounded text-xs font-mono font-medium transition-colors ${
                      selectedLeadIndex === idx
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Lead #{idx + 1}
                  </button>
                ))}
              </div>
            </div>

            {/* Active Lead Inspection Dossier */}
            {activeLead ? (
              <div className="border border-slate-800 bg-slate-950 rounded-lg p-4 space-y-4">
                
                {/* Header Info */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 border-b border-slate-800 pb-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider font-mono ${
                        activeLead.threat_level === 'CRITICAL'
                          ? 'bg-rose-950/80 text-rose-400 border border-rose-800'
                          : activeLead.threat_level === 'HIGH'
                            ? 'bg-amber-950/80 text-amber-400 border border-amber-800'
                            : 'bg-slate-800 text-slate-300 border border-slate-700'
                      }`}>
                        {activeLead.threat_level} Priority
                      </span>
                      <span className="text-xs font-mono text-slate-400">
                        {activeLead.lead_id}
                      </span>
                    </div>
                    <h3 className="text-sm font-bold text-slate-100">
                      {activeLead.title}
                    </h3>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => onInspectLeadSubgraph && onInspectLeadSubgraph(activeLead)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-medium transition-colors"
                      title="Inspect evidence subgraph in the D3 graph explorer"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      <span>Inspect Subgraph</span>
                    </button>

                    <button
                      onClick={() => onOpenBSACertificate && onOpenBSACertificate(activeLead)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors"
                      title="Open Section 63 BSA Certificate for this lead"
                    >
                      <Printer className="w-3.5 h-3.5" />
                      <span>Export BSA Certificate</span>
                    </button>
                  </div>
                </div>

                {/* Narrative Summary */}
                <div>
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                    Evidentiary Findings
                  </div>
                  <div className="text-xs text-slate-200 leading-relaxed bg-slate-900 p-3 rounded border border-slate-800 font-sans">
                    {activeLead.narrative_summary}
                  </div>
                </div>

                {/* Primary Suspect & Subgraph Overview */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 bg-slate-900 border border-slate-800 rounded">
                    <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                      Primary Suspect Record
                    </div>
                    <div className="text-slate-100 font-semibold flex items-center gap-1.5">
                      <span>{activeLead.primary_suspect?.canonical_name || 'Unidentified'}</span>
                      <span className="text-[10px] font-mono text-slate-400">
                        ({activeLead.primary_suspect?.canonical_id})
                      </span>
                    </div>
                    {activeLead.primary_suspect?.resolved_aliases?.length > 0 && (
                      <div className="text-[11px] text-amber-300 mt-1 font-sans">
                        Aliases: {activeLead.primary_suspect.resolved_aliases.join(', ')}
                      </div>
                    )}
                  </div>

                  <div className="p-3 bg-slate-900 border border-slate-800 rounded">
                    <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                      Evidence Subgraph Metrics
                    </div>
                    <div className="text-slate-200 font-mono text-xs">
                      Nodes: {activeLead.evidence_subgraph?.nodes?.length || 0} · Edges: {activeLead.evidence_subgraph?.edges?.length || 0}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-1">
                      Taxonomy: Explicit Transacted / Document Provenance
                    </div>
                  </div>
                </div>

                {/* Statutory Recommendations */}
                <div>
                  <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                    Recommended Statutory Actions (Investigator Review)
                  </div>
                  <div className="space-y-1">
                    {activeLead.actionable_recommendations?.map((rec, rIdx) => (
                      <div 
                        key={rIdx}
                        className="text-xs text-slate-300 bg-slate-900 border border-slate-800/80 p-2 rounded flex items-start gap-2"
                      >
                        <span className="text-blue-400 font-mono font-bold mt-0.5">•</span>
                        <span>{rec}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Section 63 BSA Digital Hash */}
                <div className="pt-2 border-t border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[11px] text-slate-400">
                  <div className="flex items-center gap-1.5 font-mono">
                    <Fingerprint className="w-3.5 h-3.5 text-slate-500" />
                    <span className="text-slate-500">SHA-256 Custody Seal:</span>
                    <span className="text-slate-300">{activeLead.section_63_bsa_custody_hash || activeLead.custody_hash}</span>
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono uppercase">
                    Sec. 63 BSA Admissible
                  </span>
                </div>

              </div>
            ) : (
              <div className="p-6 text-center text-slate-500 text-xs">
                Select a lead to inspect details.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
