import React, { useState, useEffect } from 'react';
import { 
  Play, 
  CheckCircle2, 
  AlertTriangle, 
  FileText, 
  ArrowRight, 
  RefreshCw, 
  Search, 
  ExternalLink, 
  Clock, 
  Fingerprint, 
  Printer, 
  HelpCircle,
  Building,
  User,
  CreditCard,
  PhoneCall,
  ShieldCheck,
  Edit3
} from 'lucide-react';
import pipelineData from '../data/pipeline_data.json';

export default function PipelineWorkbench({ 
  onInspectLeadSubgraph, 
  onOpenBSACertificate 
}) {
  const [selectedCaseKey, setSelectedCaseKey] = useState('fir');
  const [isEditingCustom, setIsEditingCustom] = useState(false);
  const [customText, setCustomText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeStageIndex, setActiveStageIndex] = useState(4); // 0 to 4
  const [pipelineResult, setPipelineResult] = useState(null);
  const [selectedLeadIndex, setSelectedLeadIndex] = useState(0);

  // Load precomputed benchmark case data on selection
  useEffect(() => {
    if (!isEditingCustom && pipelineData?.precomputed_runs?.[selectedCaseKey]) {
      setPipelineResult(pipelineData.precomputed_runs[selectedCaseKey]);
      setSelectedLeadIndex(0);
    }
  }, [selectedCaseKey, isEditingCustom]);

  // Case files to test with
  const caseFiles = [
    {
      key: 'fir',
      title: 'FIR No. 881: Cyber Fraud & Mule Network',
      sourceType: 'Police FIR (Unstructured Text)',
      summary: 'Cyber police complaint mentioning Rahul Joshi (written as राहुल जोशी), 12 feeder accounts, and collector A00013.',
      tag: 'Mule Ring'
    },
    {
      key: 'structuring',
      title: 'Bank Alert: Structuring & Smurfing',
      sourceType: 'Transaction Feed',
      summary: '6 rapid deposits between ₹9,200 and ₹9,900 across accounts A00069–A00074 to avoid regulatory reporting.',
      tag: 'Smurfing'
    },
    {
      key: 'cdr',
      title: 'Telecom Alert: 48h Call Surge',
      sourceType: 'CDR Call Detail Records',
      summary: 'High-frequency coordination calls between suspect phone PH04296 and associates prior to the cyber incident.',
      tag: 'Call Surge'
    },
    {
      key: 'scatter',
      title: 'Bank Alert: Scatter-Gather Layering',
      sourceType: 'Transaction Feed',
      summary: 'Account A00055 splitting ₹60,000 across 4 intermediary accounts, reconverging into collector A00064.',
      tag: 'Layering'
    }
  ];

  const currentCase = pipelineData?.samples?.[selectedCaseKey];

  // Process Document / Run Pipeline simulation
  const handleProcessDocument = () => {
    setIsProcessing(true);
    setActiveStageIndex(0);

    const stepInterval = 350;
    let step = 0;

    const timer = setInterval(() => {
      step += 1;
      if (step <= 4) {
        setActiveStageIndex(step);
      } else {
        clearInterval(timer);
        setIsProcessing(false);
        const runData = pipelineData?.precomputed_runs?.[selectedCaseKey];
        if (runData) {
          setPipelineResult(runData);
        }
      }
    }, stepInterval);
  };

  const activeLead = pipelineResult?.leads?.[selectedLeadIndex] || pipelineResult?.leads?.[0];

  const pipelineStages = [
    { num: 1, title: 'Extract Entities', desc: 'Find names, accounts, phones & amounts' },
    { num: 2, title: 'Match Aliases', desc: 'Link Hindi/Devanagari names to police records' },
    { num: 3, title: 'Update Graph', desc: 'Connect evidence to the knowledge graph' },
    { num: 4, title: 'Detect Patterns', desc: 'Check for mule rings, smurfing & call spikes' },
    { num: 5, title: 'Generate Leads', desc: 'Formulate action items for the officer' }
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 md:p-6 text-slate-100">
      
      {/* Top Banner: Explaining the System to a Human */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-900/60 text-blue-300 border border-blue-700/50">
                Core Investigation Pipeline
              </span>
              <span className="text-slate-500">•</span>
              <span className="text-xs text-slate-400">
                Bharatiya Sakshya Adhiniyam, 2023 · Sec. 63 Compliant
              </span>
            </div>
            <h1 className="text-xl font-bold text-slate-100">
              From Raw Evidence to Actionable Police Leads
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
              Feed in an FIR complaint, bank transaction log, or phone records. The system reads the evidence, resolves suspect identities across languages (including Hindi/Devanagari), flags criminal patterns, and gives you verified leads ready for action.
            </p>
          </div>

          <button
            onClick={handleProcessDocument}
            disabled={isProcessing}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-semibold shadow transition-all ${
              isProcessing
                ? 'bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700'
                : 'bg-blue-600 hover:bg-blue-500 text-white active:scale-95'
            }`}
          >
            {isProcessing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin text-blue-300" />
                <span>Running Step {activeStageIndex + 1} of 5...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                <span>Process Evidence & Find Leads</span>
              </>
            )}
          </button>
        </div>

        {/* Human Progress Tracker */}
        <div className="mt-5 pt-4 border-t border-slate-800 grid grid-cols-2 sm:grid-cols-5 gap-2">
          {pipelineStages.map((stage, idx) => {
            const isCompleted = activeStageIndex >= idx;
            const isCurrent = activeStageIndex === idx && isProcessing;
            return (
              <div
                key={idx}
                className={`p-2.5 rounded-lg border text-left transition-all ${
                  isCurrent
                    ? 'bg-blue-950/70 border-blue-500 text-blue-200'
                    : isCompleted
                      ? 'bg-slate-800/80 border-slate-700 text-slate-200'
                      : 'bg-slate-900/40 border-slate-800 text-slate-500'
                }`}
              >
                <div className="flex items-center justify-between text-xs font-semibold mb-0.5">
                  <span>{stage.num}. {stage.title}</span>
                  {isCompleted && <CheckCircle2 className="w-3.5 h-3.5 text-blue-400" />}
                </div>
                <div className="text-[11px] text-slate-400 truncate leading-tight">
                  {stage.desc}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Grid: Input on Left, Results & Leads on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* Left Column: Input Selection & Document View */}
        <div className="lg:col-span-5 space-y-4">
          
          {/* Case File Selector */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-blue-400" />
                <span>Select Case File or Feed</span>
              </span>
              <span className="text-[11px] text-slate-400">4 Sample Cases</span>
            </div>

            <div className="space-y-2">
              {caseFiles.map((c) => {
                const isSelected = selectedCaseKey === c.key && !isEditingCustom;
                return (
                  <button
                    key={c.key}
                    onClick={() => {
                      setIsEditingCustom(false);
                      setSelectedCaseKey(c.key);
                      setActiveStageIndex(4);
                    }}
                    className={`w-full text-left p-3 rounded-lg border transition-all ${
                      isSelected
                        ? 'bg-slate-800 border-blue-500 text-slate-100 shadow-sm'
                        : 'bg-slate-950/60 border-slate-800 hover:bg-slate-800/50 hover:border-slate-700 text-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold">{c.title}</span>
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-blue-300 border border-slate-700 font-mono">
                        {c.tag}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                      {c.summary}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Raw Document / Evidence Inspector */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                <FileText className="w-4 h-4 text-slate-400" />
                <span>Original Evidence Content</span>
              </span>
              <span className="text-[10px] font-mono text-slate-400">
                {currentCase?.source_type}
              </span>
            </div>

            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-300 max-h-72 overflow-y-auto leading-relaxed select-text whitespace-pre-wrap">
              {currentCase?.raw_text ? currentCase.raw_text.trim() : JSON.stringify(currentCase?.records || currentCase, null, 2)}
            </div>
            
            <p className="text-[11px] text-slate-500 italic">
              Notice: The text above contains Devanagari script names like 'राहुल जोशी' alongside account numbers.
            </p>
          </div>
        </div>

        {/* Right Column: Findings & Police Leads */}
        <div className="lg:col-span-7 space-y-4">

          {/* Quick Metrics Bar */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <div className="text-[11px] text-slate-400 font-medium">Entities Found</div>
              <div className="text-lg font-bold text-slate-100 font-mono mt-0.5">
                {(pipelineResult?.extracted_entities?.accounts?.length || 0) + 
                 (pipelineResult?.extracted_entities?.phones?.length || 0) + 
                 (pipelineResult?.extracted_entities?.persons?.length || 0)}
              </div>
              <div className="text-[10px] text-slate-500 truncate">Accounts, Phones, Names</div>
            </div>

            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <div className="text-[11px] text-slate-400 font-medium">Aliases Matched</div>
              <div className="text-lg font-bold text-blue-400 font-mono mt-0.5">
                {pipelineResult?.resolved_entities?.length || 0}
              </div>
              <div className="text-[10px] text-slate-500 truncate">Hindi & initials resolved</div>
            </div>

            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <div className="text-[11px] text-slate-400 font-medium">Network Connections</div>
              <div className="text-lg font-bold text-slate-100 font-mono mt-0.5">
                {pipelineResult?.graph_state?.summary?.total_edges || 0}
              </div>
              <div className="text-[10px] text-slate-500 truncate">Money flows & calls</div>
            </div>

            <div className="p-3 rounded-lg bg-slate-900 border border-slate-800">
              <div className="text-[11px] text-slate-400 font-medium">Actionable Leads</div>
              <div className="text-lg font-bold text-amber-400 font-mono mt-0.5">
                {pipelineResult?.leads?.length || 0} Leads
              </div>
              <div className="text-[10px] text-slate-500 truncate">For officer review</div>
            </div>
          </div>

          {/* Identity Match Card (Explaining the Devanagari connection) */}
          {pipelineResult?.resolved_entities && pipelineResult.resolved_entities.length > 0 && (
            <div className="p-3.5 bg-slate-900 border border-slate-800 rounded-xl space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-bold text-slate-300 uppercase tracking-wider">
                <User className="w-4 h-4 text-blue-400" />
                <span>Identity & Alias Matching Result</span>
              </div>
              <div className="space-y-1.5">
                {pipelineResult.resolved_entities.map((rp, idx) => (
                  <div 
                    key={idx}
                    className="p-2 rounded bg-slate-950 border border-slate-800 flex items-center justify-between text-xs"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-amber-300 font-medium font-sans">"{rp.raw_mention}"</span>
                      <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
                      <span className="text-slate-100 font-semibold">{rp.canonical_name}</span>
                      <span className="text-slate-400 font-mono text-[11px]">({rp.canonical_id})</span>
                    </div>
                    <span className="text-[11px] text-blue-400 font-medium">
                      {Math.round(rp.confidence * 100)}% Match Confidence
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Leads Section */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Generated Investigative Leads
              </span>

              {/* Lead Selector Pills */}
              <div className="flex items-center gap-1">
                {pipelineResult?.leads?.map((l, idx) => (
                  <button
                    key={l.lead_id}
                    onClick={() => setSelectedLeadIndex(idx)}
                    className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${
                      selectedLeadIndex === idx
                        ? 'bg-blue-600 text-white font-semibold'
                        : 'bg-slate-800 text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Lead #{idx + 1}
                  </button>
                ))}
              </div>
            </div>

            {/* Active Lead Card */}
            {activeLead ? (
              <div className="bg-slate-950 border border-slate-800 rounded-lg p-4 space-y-4">
                
                {/* Lead Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase font-mono tracking-wider ${
                        activeLead.threat_level === 'CRITICAL'
                          ? 'bg-red-950/80 text-red-400 border border-red-800'
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
                      className="flex items-center gap-1 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors"
                      title="View the suspect accounts on the interactive network map"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      <span>View on Network Map</span>
                    </button>

                    <button
                      onClick={() => onOpenBSACertificate && onOpenBSACertificate(activeLead)}
                      className="flex items-center gap-1 px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors"
                      title="Open Section 63 BSA legal certificate for court"
                    >
                      <Printer className="w-3.5 h-3.5" />
                      <span>Section 63 BSA Report</span>
                    </button>
                  </div>
                </div>

                {/* Case Summary in Plain Human Language */}
                <div>
                  <h4 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                    What Happened (Summary of Findings)
                  </h4>
                  <div className="text-xs text-slate-200 leading-relaxed bg-slate-900 p-3 rounded border border-slate-800">
                    {activeLead.narrative_summary}
                  </div>
                </div>

                {/* Primary Suspect Details */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 bg-slate-900 border border-slate-800 rounded space-y-1">
                    <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                      Primary Suspect
                    </div>
                    <div className="font-semibold text-slate-100 flex items-center gap-1.5">
                      <span>{activeLead.primary_suspect?.canonical_name || 'Unidentified'}</span>
                      <span className="text-slate-400 font-mono text-[11px]">
                        ({activeLead.primary_suspect?.canonical_id})
                      </span>
                    </div>
                    {activeLead.primary_suspect?.resolved_aliases?.length > 0 && (
                      <div className="text-[11px] text-amber-300">
                        Aliases: {activeLead.primary_suspect.resolved_aliases.join(', ')}
                      </div>
                    )}
                  </div>

                  <div className="p-3 bg-slate-900 border border-slate-800 rounded space-y-1">
                    <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                      Evidence Trail Found
                    </div>
                    <div className="font-mono text-slate-200">
                      {activeLead.evidence_subgraph?.nodes?.length || 0} accounts/parties involved
                    </div>
                    <div className="text-slate-400 text-[11px]">
                      {activeLead.evidence_subgraph?.edges?.length || 0} documented transactions linking them
                    </div>
                  </div>
                </div>

                {/* What the Officer Should Do (Actionable Next Steps) */}
                <div>
                  <h4 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                    Recommended Police Actions
                  </h4>
                  <div className="space-y-1.5">
                    {activeLead.actionable_recommendations?.map((rec, rIdx) => (
                      <div 
                        key={rIdx}
                        className="text-xs text-slate-300 bg-slate-900 border border-slate-800 p-2.5 rounded flex items-start gap-2"
                      >
                        <span className="text-blue-400 font-bold mt-0.5">•</span>
                        <span>{rec}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Court Admissibility Seal */}
                <div className="pt-2 border-t border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-[11px] text-slate-400">
                  <div className="flex items-center gap-1.5 font-mono">
                    <Fingerprint className="w-3.5 h-3.5 text-slate-500" />
                    <span className="text-slate-500">Evidence SHA-256 Seal:</span>
                    <span className="text-slate-300">{activeLead.section_63_bsa_custody_hash || activeLead.custody_hash}</span>
                  </div>
                  <span className="text-[10px] text-slate-500 font-mono uppercase">
                    Tamper-Evident Court Record
                  </span>
                </div>

              </div>
            ) : (
              <div className="p-8 text-center text-slate-500 text-xs">
                Select a case and click "Process Evidence & Find Leads" to generate findings.
              </div>
            )}

          </div>

        </div>

      </div>

    </div>
  );
}
