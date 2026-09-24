import React, { useState } from 'react';
import { 
  ShieldAlert, 
  Search, 
  Network, 
  Flame, 
  GitBranch, 
  Languages, 
  FileText, 
  Sparkles, 
  Printer, 
  CheckCircle2,
  AlertTriangle,
  Workflow
} from 'lucide-react';

export default function Header({ 
  activeTab, 
  setActiveTab, 
  onStartDemo, 
  onOpenBSA,
  searchQuery,
  setSearchQuery,
  onSearchSelect
}) {
  const [isSearchFocused, setIsSearchFocused] = useState(false);

  const tabs = [
    { id: 'pipeline', label: 'Input-to-Leads Pipeline', icon: Workflow },
    { id: 'network', label: 'Network Graph Explorer', icon: Network },
    { id: 'typologies', label: 'Typologies & Anomalies', icon: Flame },
    { id: 'link_prediction', label: 'AI Link Prediction Studio', icon: GitBranch },
    { id: 'entity_resolution', label: 'Cross-Lingual Entity Resolution', icon: Languages },
    { id: 'cases', label: 'Active FIRs & Cases', icon: FileText },
  ];

  return (
    <header className="border-b border-[rgba(255,255,255,0.08)] bg-[#0b1120]/90 backdrop-blur-md sticky top-0 z-50 px-6 py-3">
      {/* Top Bar: Branding & High-Priority Notice */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/20 border border-sky-400/30">
            <ShieldAlert className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-slate-100 tracking-tight flex items-center gap-2">
                I4C · Criminal Network Intelligence System
              </h1>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-sky-500/10 text-sky-400 border border-sky-500/30">
                SIH PS 189
              </span>
            </div>
            <p className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Live Evidentiary Knowledge Graph · Governing Principle: <strong className="text-emerald-400 font-semibold">Leads, Not Proof</strong>
            </p>
          </div>
        </div>

        {/* Global Search & Action Buttons */}
        <div className="flex items-center gap-3">
          <div className="relative w-64 md:w-80">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              placeholder="Search Entity ID, Phone, Account, Name, FIR..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => setIsSearchFocused(true)}
              onBlur={() => setTimeout(() => setIsSearchFocused(false), 200)}
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-900/80 border border-slate-700/60 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-all font-mono"
            />
          </div>

          <button
            onClick={onStartDemo}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 text-white text-xs font-semibold shadow-md shadow-amber-500/20 transition-all transform hover:-translate-y-0.5"
            title="Start guided judge presentation narrative"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Guided Demo (Judges Tour)</span>
          </button>

          <button
            onClick={onOpenBSA}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-md shadow-emerald-600/20 transition-all"
            title="Generate Section 63 BSA Electronic Record Certificate"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Export Section 63 BSA</span>
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav className="flex items-center gap-1 overflow-x-auto pt-1 no-scrollbar border-t border-slate-800/60">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-medium transition-all whitespace-nowrap ${
                isActive
                  ? 'bg-sky-500/15 text-sky-400 border border-sky-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-sky-400' : 'text-slate-400'}`} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>
    </header>
  );
}
