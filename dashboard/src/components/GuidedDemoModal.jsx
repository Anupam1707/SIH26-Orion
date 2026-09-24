import React, { useState } from 'react';
import { 
  X, 
  Sparkles, 
  ArrowRight, 
  ArrowLeft, 
  CheckCircle2, 
  AlertTriangle, 
  Split, 
  Flame, 
  FileCheck,
  Play
} from 'lucide-react';

export default function GuidedDemoModal({ onClose, onSelectStep }) {
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    {
      title: 'Step 1: Mule Fan-In Detection (MULE_01)',
      subtitle: 'Rule-Based, Zero ML, 100% Explainable',
      typologyId: 'MULE_01',
      badge: 'Tier 1 Rule-Based',
      badgeColor: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
      description: '12 distinct source accounts converge on mule collector account A00013 within 30 hours, transferring an aggregate of ₹161,025. A00013 then rapidly forwards the funds to exit cashout account A00014.',
      judgeNote: 'Demonstrates baseline rule-based detection catching complex convergence without ML false positives.',
      actionLabel: 'Load Mule Fan-In Subgraph'
    },
    {
      title: 'Step 2: Unsupervised OddBall Scatter (SCATTER_GATHER_01)',
      subtitle: 'Structural Power-Law Outlier Scoring (Akoglu et al.)',
      typologyId: 'SCATTER_GATHER_01',
      badge: 'Tier 2a Unsupervised',
      badgeColor: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
      description: 'Scatter source A00055 rapidly disperses illicit funds across 9 destination accounts within 2.6 hours. Without being given any rules or training labels, the OddBall algorithm flagged A00055 at rank 6/532 (top 1.1% of all accounts in the graph).',
      judgeNote: 'Clean unsupervised win — discovering zero-day money dispersal solely from topological egonet distortion.',
      actionLabel: 'Load Scatter Source Subgraph'
    },
    {
      title: 'Step 3: Topological Reachability Bridge (A00013 ↔ A00055)',
      subtitle: 'Shortest Path Traversal + Non-Chronological Caveat',
      typologyId: 'TOPOLOGICAL_BRIDGE',
      badge: 'Inferred Topological Link',
      badgeColor: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
      description: 'A length-5 graph path connects mule controller P00231 (A00013) to scatter kingpin P02240 (A00055) via pass-through accounts A01253 and A00820. However, the transaction timestamps occur non-chronologically (Sep 2024 ➔ Jun 2025 ➔ Feb 2024).',
      judgeNote: 'Crucial ethical demonstration: The system flags this as an Inferred Topological Connection rather than an Explicit Money Trail, preventing judicial perjury.',
      actionLabel: 'Inspect Non-Chronological Bridge'
    },
    {
      title: 'Step 4: Structuring Ring & Scientific Limitations (STRUCTURING_01)',
      subtitle: 'Louvain Fragmentation vs 48h Temporal Burst Scoring',
      typologyId: 'STRUCTURING_01',
      badge: 'Tier 2b Temporal Scoring',
      badgeColor: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
      description: '6 accounts (A00069–A00074) execute 10 smurfing transactions each at exact 60-minute intervals in the ₹9,000–₹9,900 band (just under ₹10k reporting limits). Louvain community detection failed by splitting them across 6 separate communities. The 48h temporal composite burst detector unified all 6 accounts together at ranks 1–6.',
      judgeNote: 'Honest scientific transparency: Demonstrating why single algorithms fail and why multi-tier defense is required.',
      actionLabel: 'Load Structuring Ring Subgraph'
    },
    {
      title: 'Step 5: Court-Ready Section 63 BSA Lead Generation',
      subtitle: 'Electronic Record Certificate & SHA-256 Custody Hash',
      typologyId: 'BSA_REPORT',
      badge: 'Legal Admissibility',
      badgeColor: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
      description: 'Generates a formal, printable electronic lead certificate under Section 63 of Bharatiya Sakshya Adhiniyam, 2023 with cryptographic SHA-256 digital fingerprint, complete evidence provenance chain, and statutory "Leads, Not Proof" legal disclaimers.',
      judgeNote: 'Converts abstract graph math into legally actionable evidentiary dossiers for law enforcement.',
      actionLabel: 'View Section 63 BSA Lead Certificate'
    }
  ];

  const current = steps[currentStep];

  const handleExecute = () => {
    onSelectStep(current);
    onClose();
  };

  React.useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
      else if (e.key === 'ArrowRight') setCurrentStep(prev => Math.min(steps.length - 1, prev + 1));
      else if (e.key === 'ArrowLeft') setCurrentStep(prev => Math.max(0, prev - 1));
      else if (e.key === 'Enter') handleExecute();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentStep, onClose]);

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="bg-[#0e1629] border border-slate-700 w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/80">
          <div className="flex items-center gap-2 text-amber-400 font-bold text-xs uppercase tracking-wider">
            <Sparkles className="w-4 h-4" />
            <span>SIH26 Hackathon Judge & Evaluator Demo Tour</span>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Stepper Progress */}
        <div className="px-6 pt-4 flex items-center justify-between border-b border-slate-800 pb-3">
          {steps.map((s, idx) => (
            <button
              key={idx}
              onClick={() => setCurrentStep(idx)}
              className={`flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-lg transition-all ${
                currentStep === idx
                  ? 'bg-amber-500 text-black shadow-md shadow-amber-500/30 font-bold'
                  : (idx < currentStep ? 'text-emerald-400' : 'text-slate-500')
              }`}
            >
              <span>{idx + 1}</span>
            </button>
          ))}
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border ${current.badgeColor}`}>
              {current.badge}
            </span>
            <span className="text-xs text-slate-400 mono">
              Step {currentStep + 1} of {steps.length}
            </span>
          </div>

          <div>
            <h3 className="text-lg font-bold text-white tracking-tight">
              {current.title}
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              {current.subtitle}
            </p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 text-xs text-slate-300 leading-relaxed">
            {current.description}
          </div>

          <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-200 space-y-1">
            <strong className="block text-amber-300 uppercase text-[10px] tracking-wider">
              Judge Evaluation Focus:
            </strong>
            <p>{current.judgeNote}</p>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/60 flex items-center justify-between">
          <button
            onClick={() => setCurrentStep(prev => Math.max(0, prev - 1))}
            disabled={currentStep === 0}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white disabled:opacity-30 disabled:pointer-events-none"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Previous</span>
          </button>

          <button
            onClick={handleExecute}
            className="flex items-center gap-2 px-5 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white font-bold text-xs shadow-lg shadow-amber-500/25 transition-all transform hover:-translate-y-0.5"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>{current.actionLabel}</span>
          </button>

          <button
            onClick={() => setCurrentStep(prev => Math.min(steps.length - 1, prev + 1))}
            disabled={currentStep === steps.length - 1}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-400 hover:text-white disabled:opacity-30 disabled:pointer-events-none"
          >
            <span>Next</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
