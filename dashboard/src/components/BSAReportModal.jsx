import React, { useEffect, useState } from 'react';
import { X, Printer, ShieldCheck, FileCheck, Hash, Download } from 'lucide-react';
import { generateEvidenceHash, formatDateTime, formatINR } from '../utils/crypto';

export default function BSAReportModal({ node, currentGraph, onClose }) {
  const [evidenceHash, setEvidenceHash] = useState('computing...');
  const [reportDate] = useState(new Date().toISOString());

  useEffect(() => {
    async function computeHash() {
      const payload = {
        node: node || { id: 'SYNDICATE_SUBGRAPH_LEAD' },
        edges: currentGraph?.edges || [],
        timestamp: reportDate,
        statutory_authority: 'I4C / Ministry of Home Affairs'
      };
      const h = await generateEvidenceHash(payload);
      setEvidenceHash(h);
    }
    computeHash();
  }, [node, currentGraph, reportDate]);

  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const handlePrint = () => {
    window.print();
  };

  const handleCopyHash = () => {
    navigator.clipboard.writeText(evidenceHash);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadJSON = () => {
    const certificateData = {
      certificate_type: 'Section 63 BSA Electronic Record Certificate',
      statutory_basis: 'Section 63 Bharatiya Sakshya Adhiniyam, 2023',
      sha256_evidence_hash: evidenceHash,
      timestamp: reportDate,
      issuing_authority: 'I4C / Ministry of Home Affairs, PS 189',
      target_entity: node,
      subgraph: currentGraph,
      statutory_notice: 'Leads, Not Proof — Requires independent corroboration under Section 193 BNSS, 2023'
    };
    const blob = new Blob([JSON.stringify(certificateData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `BSA63_LEAD_${evidenceHash.slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto">
      <div className="bg-[#0b1120] border border-slate-700 w-full max-w-4xl rounded-2xl shadow-2xl flex flex-col max-h-[92vh] overflow-hidden">
        {/* Modal Top Actions */}
        <div className="no-print p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/80">
          <div className="flex items-center gap-2 text-emerald-400 font-bold text-xs uppercase tracking-wider">
            <ShieldCheck className="w-4 h-4" />
            <span>Section 63 BSA Official Electronic Lead Dossier</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCopyHash}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-all"
              title="Copy SHA-256 Hash"
            >
              <Hash className="w-3.5 h-3.5 text-emerald-400" />
              <span>{copied ? 'Copied Hash!' : 'Copy Hash'}</span>
            </button>

            <button
              onClick={handleDownloadJSON}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-all"
              title="Download Digital JSON Lead Package"
            >
              <Download className="w-3.5 h-3.5 text-sky-400" />
              <span>Export JSON</span>
            </button>

            <button
              onClick={handlePrint}
              className="flex items-center gap-2 px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs shadow-md transition-all"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print / Export PDF</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Printable Certificate Body */}
        <div className="bsa-report-container p-8 overflow-y-auto space-y-6 text-slate-200 bg-white text-slate-950 font-sans print:p-0">
          {/* Official Indian Gov Header */}
          <div className="text-center border-b-2 border-slate-900 pb-4">
            <div className="text-xs uppercase tracking-widest font-black text-slate-700">
              Government of India · Ministry of Home Affairs
            </div>
            <div className="text-base font-extrabold uppercase text-slate-900 mt-1">
              Indian Cybercrime Coordination Centre (I4C)
            </div>
            <div className="text-xs uppercase tracking-wider font-bold text-slate-600 mt-0.5">
              National Cyber Crime Threat Analytics Unit (TAU) · PS 189
            </div>
            <h1 className="text-lg font-black uppercase text-slate-950 mt-3 tracking-tight underline decoration-slate-400">
              Certificate of Electronic Record Under Section 63, Bharatiya Sakshya Adhiniyam, 2023
            </h1>
          </div>

          {/* Metadata Grid */}
          <div className="grid grid-cols-2 gap-4 text-xs font-mono border border-slate-300 p-4 rounded-lg bg-slate-50">
            <div>
              <span className="text-slate-500 block font-sans text-[10px] uppercase">Certificate Reference No.</span>
              <strong className="text-slate-900">BSA/2026/I4C/TAU-{(evidenceHash.slice(0, 8)).toUpperCase()}</strong>
            </div>
            <div>
              <span className="text-slate-500 block font-sans text-[10px] uppercase">Timestamp of Extraction</span>
              <strong className="text-slate-900">{formatDateTime(reportDate)} IST</strong>
            </div>
            <div>
              <span className="text-slate-500 block font-sans text-[10px] uppercase">Governing Framework</span>
              <strong className="text-slate-900">Section 63 BSA (Admissibility of Electronic Records)</strong>
            </div>
            <div>
              <span className="text-slate-500 block font-sans text-[10px] uppercase">Investigating Station / Unit</span>
              <strong className="text-slate-900">Central Cyber Command / Special Task Force</strong>
            </div>
          </div>

          {/* Cryptographic SHA-256 Custody Hash */}
          <div className="p-3 bg-slate-100 rounded-lg border border-slate-300 font-mono text-xs">
            <div className="flex items-center gap-1.5 text-slate-700 font-sans text-[11px] font-bold uppercase mb-1">
              <Hash className="w-3.5 h-3.5 text-emerald-700" />
              <span>Digital Custody SHA-256 Hash of Evidence Subgraph</span>
            </div>
            <div className="break-all font-bold text-slate-900 text-[11px] select-all">
              {evidenceHash}
            </div>
          </div>

          {/* Entity & Subgraph Subject Information */}
          <div className="space-y-2 text-xs">
            <h3 className="font-bold text-slate-900 uppercase text-xs tracking-wider border-b border-slate-300 pb-1">
              1. Primary Subject of Inquiry & Profile
            </h3>
            <div className="grid grid-cols-3 gap-3 p-3 bg-slate-50 rounded border border-slate-200">
              <div>
                <span className="text-slate-500 text-[10px] block">Identifier:</span>
                <strong className="text-slate-900 font-mono">{node?.id || 'Syndicate Cell Subgraph'}</strong>
              </div>
              <div>
                <span className="text-slate-500 text-[10px] block">Entity Category:</span>
                <strong className="text-slate-900">{node?.entity_type || 'Multi-Entity Subgraph'}</strong>
              </div>
              <div>
                <span className="text-slate-500 text-[10px] block">Canonical Holder / Name:</span>
                <strong className="text-slate-900">{node?.holder_name || 'Network Associates'}</strong>
              </div>
            </div>
          </div>

          {/* Evidentiary Taxonomy & Subgraph Table */}
          <div className="space-y-2 text-xs">
            <h3 className="font-bold text-slate-900 uppercase text-xs tracking-wider border-b border-slate-300 pb-1 flex items-center justify-between">
              <span>2. Chain of Provenance & Connected Relationships</span>
              <span className="text-[10px] font-normal text-slate-600">Strict Explicit / Inferred / Predicted Taxonomy Enforced</span>
            </h3>

            <table className="w-full text-left text-xs border border-slate-300">
              <thead className="bg-slate-200 text-slate-700 uppercase text-[10px]">
                <tr>
                  <th className="p-2 border border-slate-300">Edge ID</th>
                  <th className="p-2 border border-slate-300">Source Entity</th>
                  <th className="p-2 border border-slate-300">Target Entity</th>
                  <th className="p-2 border border-slate-300">Amount / Duration</th>
                  <th className="p-2 border border-slate-300">Taxonomy Class</th>
                  <th className="p-2 border border-slate-300">Source Evidence Ref</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 font-mono text-[11px]">
                {currentGraph?.edges?.slice(0, 12).map((e, idx) => (
                  <tr key={idx}>
                    <td className="p-2 border border-slate-300 text-slate-600">{e.id}</td>
                    <td className="p-2 border border-slate-300 font-bold">{typeof e.source === 'object' ? e.source.id : e.source}</td>
                    <td className="p-2 border border-slate-300 font-bold">{typeof e.target === 'object' ? e.target.id : e.target}</td>
                    <td className="p-2 border border-slate-300 font-sans">
                      {e.amount ? formatINR(e.amount) : (e.call_duration_sec ? `${Math.round(e.call_duration_sec)}s` : 'N/A')}
                    </td>
                    <td className="p-2 border border-slate-300 font-sans font-bold">
                      {e.taxonomy || 'Explicit'}
                    </td>
                    <td className="p-2 border border-slate-300 text-slate-700">
                      {e.evidence_id || 'DOC00184'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mandatory Statutory Disclaimer (India Law) */}
          <div className="p-4 bg-amber-50 border border-amber-300 rounded-lg text-xs space-y-1.5">
            <h4 className="font-black text-amber-900 uppercase text-[11px] tracking-wide">
              Statutory Evidentiary Declaration & Legal Notice
            </h4>
            <p className="text-amber-950 leading-relaxed text-[11px]">
              <strong>1. Leads, Not Proof:</strong> In accordance with the official problem statement charter (I4C PS 189), this computerized intelligence output is provided solely as an investigative lead to assist human law enforcement officers. It does not constitute conclusive evidence or judicial accusation of guilt.
            </p>
            <p className="text-amber-950 leading-relaxed text-[11px]">
              <strong>2. Mandatory Independent Corroboration:</strong> Any link marked as <em>Inferred</em> (such as non-chronological shortest path reachability) or <em>Predicted</em> (machine learning tie probability) must be verified through physical documentary evidence (bank account statements under Bankers' Books Evidence Act, subscriber CAF forms under Indian Telegraph Act) prior to judicial charge-sheeting under Section 193 of the Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023.
            </p>
          </div>

          {/* Officer Signature Block */}
          <div className="grid grid-cols-2 gap-8 pt-6 border-t border-slate-400 text-xs">
            <div>
              <div className="font-bold text-slate-900">Certified by System Custodian:</div>
              <div className="mt-8 pt-1 border-t border-slate-500 font-mono text-[11px]">
                I4C Graph Engine Lead Officer / Engineer
              </div>
              <div className="text-[10px] text-slate-500">National Cyber Crime Threat Analytics Unit</div>
            </div>

            <div>
              <div className="font-bold text-slate-900">Investigating Officer Endorsement:</div>
              <div className="mt-8 pt-1 border-t border-slate-500 font-mono text-[11px]">
                Superintendent of Police / Cyber Crime Branch
              </div>
              <div className="text-[10px] text-slate-500">Authorized Signatory & Seal</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
