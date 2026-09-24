import React, { useState } from 'react';
import { 
  Shield, 
  Search, 
  Network, 
  Flame, 
  GitBranch, 
  Languages, 
  FileText, 
  HelpCircle, 
  Printer, 
  Workflow,
  Info
} from 'lucide-react';

export default function Header({ 
  activeTab, 
  setActiveTab, 
  onStartDemo, 
  onOpenBSA,
  searchQuery,
  setSearchQuery
}) {
  const tabs = [
    { id: 'pipeline', label: 'Investigation Pipeline', icon: Workflow },
    { id: 'network', label: 'Network Map', icon: Network },
    { id: 'typologies', label: 'Fraud Patterns', icon: Flame },
    { id: 'link_prediction', label: 'Hidden Conspirators', icon: GitBranch },
    { id: 'entity_resolution', label: 'Alias Resolution', icon: Languages },
    { id: 'cases', label: 'Case Files', icon: FileText },
    { id: 'about', label: 'About & Team', icon: Info },
  ];

  return (
    <header className="border-b border-slate-800 bg-[#090d16] sticky top-0 z-50 px-6 py-2.5">
      {/* Top Bar: Clean Institutional Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-2.5">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-200">
            <Shield className="w-4 h-4 text-blue-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-bold text-slate-100 tracking-tight">
                Indian Cyber Crime Coordination Centre (I4C)
              </h1>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-blue-900/60 text-blue-300 border border-blue-700/50">
                ORION SYSTEM
              </span>
            </div>
            <p className="text-[11px] text-slate-400 flex items-center gap-1.5 mt-0.5">
              <span>Criminal Network Analysis System</span>
              <span className="text-slate-600">•</span>
              <span className="text-slate-300 font-medium">Sec. 63 BSA Mandate: Leads, Not Proof</span>
            </p>
          </div>
        </div>

        {/* Search & Actions */}
        <div className="flex items-center gap-2.5">
          <div className="relative w-64 md:w-72">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              placeholder="Search Entity ID, Account, Phone, Name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-900 border border-slate-700/80 rounded-md text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 font-mono transition-colors"
            />
          </div>

          <button
            onClick={onStartDemo}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 text-xs font-medium transition-colors"
            title="Start system guided walkthrough"
          >
            <HelpCircle className="w-3.5 h-3.5 text-slate-400" />
            <span>Operational Walkthrough</span>
          </button>

          <button
            onClick={onOpenBSA}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors"
            title="Generate Section 63 BSA Electronic Record Certificate"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Export Section 63 BSA</span>
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <nav className="flex items-center gap-1 overflow-x-auto pt-1 no-scrollbar border-t border-slate-800/80">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors whitespace-nowrap ${
                isActive
                  ? 'bg-slate-800 text-blue-400 border border-slate-700'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-blue-400' : 'text-slate-500'}`} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>
    </header>
  );
}
