import React, { useState } from 'react';
import { 
  Languages, 
  Search, 
  CheckCircle2, 
  XCircle, 
  FileCheck, 
  AlertCircle,
  HelpCircle,
  SlidersHorizontal
} from 'lucide-react';

export default function EntityResolutionWorkbench({ entityResolutionData, onSelectCandidate }) {
  const [filterType, setFilterType] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');
  const [verifiedMap, setVerifiedMap] = useState({});

  const sampleTypes = [
    { id: 'ALL', label: 'All Variants' },
    { id: 'DEVANAGARI_VARIANT', label: 'Devanagari Script (Hindi)' },
    { id: 'TRANSLITERATION_VARIANT', label: 'Transliteration Variants' },
    { id: 'OCR_CORRUPTION', label: 'OCR Scanner Corruptions' },
    { id: 'NICKNAME', label: 'Aliases & Nicknames' },
  ];

  const filtered = (entityResolutionData || []).filter(item => {
    if (filterType !== 'ALL' && item.alias_type !== filterType) return false;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      return (
        item.alias_value?.toLowerCase().includes(q) ||
        item.canonical_name?.toLowerCase().includes(q) ||
        item.entity_id?.toLowerCase().includes(q)
      );
    }
    return true;
  });

  const toggleVerification = (aliasId) => {
    setVerifiedMap(prev => ({
      ...prev,
      [aliasId]: !prev[aliasId]
    }));
  };

  return (
    <div className="flex flex-col h-full bg-[#0a0e1a] overflow-hidden">
      {/* Workbench Header */}
      <div className="px-6 py-3 border-b border-slate-800 bg-[#0e1629]/90 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Languages className="w-5 h-5 text-sky-400" />
          <div>
            <h2 className="text-base font-bold text-white tracking-tight">
              Cross-Lingual Entity Resolution & Alias Disambiguation Workbench (Module 2)
            </h2>
            <p className="text-xs text-slate-400">
              Devanagari-Latin Alignment · Phonetic OCR Denoising · Transliteration Matching
            </p>
          </div>
        </div>

        {/* Search inside entity resolution */}
        <div className="relative w-64">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            placeholder="Search alias, Hindi, or person ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-900 border border-slate-700/60 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-sky-500 font-mono"
          />
        </div>
      </div>

      <div className="p-6 overflow-y-auto space-y-4">
        {/* Methodological Overview Banner */}
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300 flex items-start justify-between">
          <div>
            <h3 className="text-sm font-bold text-white mb-1">
              Multi-Lingual Identity Disambiguation Engine
            </h3>
            <p className="max-w-3xl leading-relaxed text-slate-400">
              Criminals intentionally register bank accounts and SIM cards under phonetic transliterations (e.g. <em>Arjd. Shah</em>), Devanagari script (e.g. <em>नेहा Patel</em>), or OCR-corrupted character swaps (e.g. <em>Nikhi1 Mehta</em> with digit '1' replacing 'l'). 
              The system resolves aliases to canonical Master Person Index (MPI) profiles using phonetic Soundex, Levenshtein distance, and PAN/Aadhaar auxiliary features.
            </p>
          </div>
          <div className="p-3 rounded-lg bg-sky-500/10 border border-sky-500/30 text-sky-300 text-right mono shrink-0">
            <div className="text-lg font-black">2,400+</div>
            <div className="text-[10px]">Resolved Identifiers</div>
          </div>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          {sampleTypes.map(t => (
            <button
              key={t.id}
              onClick={() => setFilterType(t.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all ${
                filterType === t.id
                  ? 'bg-sky-500 text-white shadow-sm'
                  : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Aliases Table */}
        <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-900/40">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900 text-slate-400 uppercase text-[10px] tracking-wider border-b border-slate-800">
              <tr>
                <th className="p-3">Alias ID</th>
                <th className="p-3">Raw Alias / Variant in Evidence</th>
                <th className="p-3">Variant Classification</th>
                <th className="p-3">Resolved Canonical Person</th>
                <th className="p-3">Person ID</th>
                <th className="p-3">Match Confidence</th>
                <th className="p-3">Auxiliary Features</th>
                <th className="p-3 text-right">Analyst Verification</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
              {filtered.map((item) => {
                const isVerified = verifiedMap[item.alias_id] !== undefined ? verifiedMap[item.alias_id] : true;
                const isHindi = item.alias_type === 'DEVANAGARI_VARIANT';
                const isOCR = item.alias_type === 'OCR_CORRUPTION';

                return (
                  <tr 
                    key={item.alias_id} 
                    onClick={() => onSelectCandidate && onSelectCandidate(item)}
                    className="hover:bg-slate-800/60 cursor-pointer transition-colors group"
                  >
                    <td className="p-3 text-slate-400 group-hover:text-white">{item.alias_id}</td>
                    <td className={`p-3 text-sm font-bold ${
                      isHindi ? 'text-amber-300 font-sans text-base' : (isOCR ? 'text-rose-300' : 'text-sky-300')
                    }`}>
                      {item.alias_value}
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        isHindi 
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' 
                          : (isOCR 
                              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30' 
                              : 'bg-blue-500/20 text-blue-300 border border-blue-500/30')
                      }`}>
                        {item.alias_type}
                      </span>
                    </td>
                    <td className="p-3 font-sans font-bold text-white group-hover:text-sky-300">
                      {item.canonical_name}
                    </td>
                    <td className="p-3 text-sky-400 font-bold">
                      {item.entity_id}
                    </td>
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <div className="w-12 bg-slate-800 rounded-full h-1.5">
                          <div 
                            className="bg-emerald-400 h-1.5 rounded-full"
                            style={{ width: `${Math.round(item.confidence_score * 100)}%` }}
                          ></div>
                        </div>
                        <span className="text-emerald-400 font-bold">{Math.round(item.confidence_score * 100)}%</span>
                      </div>
                    </td>
                    <td className="p-3 text-slate-400 text-[10px]">
                      <span>PAN: {item.pan_hash}</span>
                    </td>
                    <td className="p-3 text-right">
                      <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => toggleVerification(item.alias_id)}
                          className={`px-2.5 py-1 rounded text-[10px] font-bold inline-flex items-center gap-1.5 transition-all ${
                            isVerified 
                              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' 
                              : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          }`}
                        >
                          {isVerified ? (
                            <>
                              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                              <span>Verified Lead</span>
                            </>
                          ) : (
                            <>
                              <XCircle className="w-3 h-3 text-amber-400" />
                              <span>Review Req.</span>
                            </>
                          )}
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
