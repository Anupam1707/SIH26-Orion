import React, { useState } from 'react';
import { FileText, Search, Shield, Building, Calendar, CheckCircle2 } from 'lucide-react';
import { formatDateTime } from '../utils/crypto';

export default function CasesView({ casesData, onSelectCase }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');

  const categories = ['ALL', 'Cyber', 'Economic', 'Organized Crime'];

  const filtered = (casesData || []).filter(c => {
    if (categoryFilter !== 'ALL' && c.case_type !== categoryFilter) return false;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      return (
        c.fir_number?.toLowerCase().includes(q) ||
        c.police_station?.toLowerCase().includes(q) ||
        c.jurisdiction?.toLowerCase().includes(q) ||
        c.case_category?.toLowerCase().includes(q) ||
        c.case_id?.toLowerCase().includes(q)
      );
    }
    return true;
  });

  return (
    <div className="flex flex-col h-full bg-[#0a0e1a] overflow-hidden">
      {/* Cases Header */}
      <div className="px-6 py-3 border-b border-slate-800 bg-[#0e1629]/90 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-rose-500" />
          <div>
            <h2 className="text-base font-bold text-white tracking-tight">
              Active FIRs & Investigation Case Registry
            </h2>
            <p className="text-xs text-slate-400">
              CCTNS / ICJS Integrated Records · Automated Evidence Document Provenance
            </p>
          </div>
        </div>

        <div className="relative w-64">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Search FIR, Police Station, Jurisdiction..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-900 border border-slate-700/60 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 font-mono"
          />
        </div>
      </div>

      <div className="p-6 overflow-y-auto space-y-4">
        {/* Category Pills */}
        <div className="flex items-center gap-2">
          {categories.map(cat => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                categoryFilter === cat
                  ? 'bg-rose-600 text-white shadow-sm'
                  : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              {cat === 'ALL' ? 'All Crime Types' : cat}
            </button>
          ))}
        </div>

        {/* Cases Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map(item => (
            <div
              key={item.case_id}
              onClick={() => onSelectCase && onSelectCase(item)}
              className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-rose-500/50 hover:bg-slate-900/90 transition-all flex flex-col justify-between cursor-pointer group shadow-sm hover:shadow-rose-500/10"
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-rose-400 mono">
                    {item.fir_number}
                  </span>
                  <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    {item.case_type}
                  </span>
                </div>

                <h3 className="text-sm font-bold text-white mb-2">
                  {item.case_category}
                </h3>

                <div className="space-y-1.5 text-xs text-slate-400">
                  <div className="flex items-center gap-1.5">
                    <Building className="w-3.5 h-3.5 text-slate-500" />
                    <span>{item.police_station} ({item.jurisdiction})</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Shield className="w-3.5 h-3.5 text-slate-500" />
                    <span>Investigating Unit: <strong className="text-slate-300 font-normal">{item.investigating_unit}</strong></span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Calendar className="w-3.5 h-3.5 text-slate-500" />
                    <span>Incident Date: {item.incident_date}</span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
                <span className="text-slate-500 mono">Doc: {item.source_document_id}</span>
                <span className="text-emerald-400 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>{item.case_status}</span>
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
