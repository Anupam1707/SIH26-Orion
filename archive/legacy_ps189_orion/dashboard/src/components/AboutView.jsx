import React from 'react';
import { 
  Shield, 
  Users, 
  Award, 
  FileText, 
  ExternalLink, 
  CheckCircle2, 
  Lock, 
  Cpu, 
  Database, 
  Workflow, 
  Terminal, 
  Scale, 
  Mail, 
  Github, 
  Globe 
} from 'lucide-react';

export default function AboutView() {
  return (
    <div className="flex-1 h-full overflow-y-auto p-6 max-w-5xl mx-auto space-y-8 text-slate-100 pb-16">
      
      {/* Title & Official Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-900/60 text-blue-300 border border-blue-700/50 uppercase font-mono">
            System Identity & Heritage
          </span>
          <span className="text-slate-500">•</span>
          <span className="text-xs text-slate-400">
            Indian Cyber Crime Coordination Centre (I4C) · Ministry of Home Affairs
          </span>
        </div>
        
        <h1 className="text-2xl font-bold text-slate-100 tracking-tight">
          ORION · Criminal Network Discovery & Evidentiary Analysis System
        </h1>
        
        <p className="text-sm text-slate-300 leading-relaxed max-w-3xl">
          An automated, multi-source criminal intelligence platform developed for national law enforcement agencies. 
          The platform ingests unstructured police complaints, banking transaction feeds, and telecommunication logs, 
          identifies concealed criminal syndicates through multi-tier network analytics, and generates court-admissible 
          investigative leads certified under Section 63 of the Bharatiya Sakshya Adhiniyam (BSA), 2023.
        </p>
      </div>

      {/* Smart India Hackathon (SIH) Origin Section */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center gap-2 text-base font-bold text-slate-100">
          <Award className="w-5 h-5 text-amber-400" />
          <h2>Smart India Hackathon (SIH) Genesis</h2>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed">
          ORION originated and was architected under the national <strong>Smart India Hackathon (SIH)</strong> initiative, addressing a mission-critical cybersecurity and law enforcement challenge presented by the Government of India.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2 text-xs">
          <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-1">
            <div className="text-[10px] uppercase font-mono text-slate-400">Initiative</div>
            <div className="font-semibold text-slate-100">Smart India Hackathon (SIH)</div>
            <div className="text-slate-400 text-[11px]">Government of India</div>
          </div>

          <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-1">
            <div className="text-[10px] uppercase font-mono text-slate-400">Problem Statement</div>
            <div className="font-semibold text-slate-100">SIH PS 189</div>
            <div className="text-slate-400 text-[11px]">AI-Powered Criminal Network Discovery</div>
          </div>

          <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-1">
            <div className="text-[10px] uppercase font-mono text-slate-400">Nodal Organization</div>
            <div className="font-semibold text-slate-100">I4C / Ministry of Home Affairs</div>
            <div className="text-slate-400 text-[11px]">Cyber Crime Unit, New Delhi</div>
          </div>
        </div>

        <div className="p-3.5 bg-slate-950 border border-slate-800 rounded-lg space-y-1.5 text-xs">
          <div className="font-semibold text-slate-200">The Problem Mandate:</div>
          <p className="text-slate-300 leading-relaxed">
            Police officers and cyber cells receive fragmented, heterogeneous data: handwritten/scanned FIR narratives in regional languages, bank transaction CSVs from multiple switches, and telecommunication tower dumps. Manual cross-referencing takes weeks. The challenge was to build an automated, explainable system that maps networks and produces <em>actionable leads</em> rather than black-box conclusions.
          </p>
        </div>
      </div>

      {/* Team Orion Section */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center gap-2 text-base font-bold text-slate-100">
          <Users className="w-5 h-5 text-blue-400" />
          <h2>Development Team · Team Orion</h2>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed">
          ORION was engineered by <strong>Team Orion</strong> (Project identifier: <code className="text-blue-300 font-mono">orion26-team</code>), bringing together graph database engineering, cross-lingual NLP, unsupervised graph anomaly detection, and judicial evidentiary compliance.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
          <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg space-y-2">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-slate-100 text-sm">Anupam Kanoongo</h3>
                <div className="text-xs text-blue-400">Lead Architect & Full-Stack Intelligence Engineer</div>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                Team Lead
              </span>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              Designed the end-to-end Input-to-Leads pipeline, Neo4j CKG data loaders, multi-lingual entity resolution engine, OddBall structural anomaly scorer, and courtroom-compliant Section 63 BSA export system.
            </p>

            <div className="pt-2 border-t border-slate-800/80 flex items-center gap-4 text-xs text-slate-400">
              <a 
                href="mailto:anupamkanoongo@gmail.com" 
                className="flex items-center gap-1.5 hover:text-blue-400 transition-colors"
              >
                <Mail className="w-3.5 h-3.5" />
                <span>anupamkanoongo@gmail.com</span>
              </a>
              <a 
                href="https://github.com/Anupam1707/SIH26-Orion" 
                target="_blank" 
                rel="noreferrer" 
                className="flex items-center gap-1.5 hover:text-blue-400 transition-colors"
              >
                <Github className="w-3.5 h-3.5" />
                <span>GitHub Repository</span>
              </a>
            </div>
          </div>

          <div className="p-4 bg-slate-950 border border-slate-800 rounded-lg space-y-2">
            <div>
              <h3 className="font-bold text-slate-100 text-sm">Team Orion Core</h3>
              <div className="text-xs text-slate-400">AI / ML & Cyber Forensics Engineering</div>
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              Engineered the Graph Neural Network (GNN) and Random Forest link prediction classifiers, temporal burst Z-score detectors, and interactive D3 force-directed visualizers.
            </p>

            <div className="pt-2 border-t border-slate-800/80 space-y-1 text-xs text-slate-400">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
                <span>Project Key: <strong className="text-slate-200 font-mono">orion26-team</strong></span>
              </div>
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                <span>Deployment: Firebase Production Hosting</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Core Architectural Pillars */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
        <div className="flex items-center gap-2 text-base font-bold text-slate-100">
          <Cpu className="w-5 h-5 text-indigo-400" />
          <h2>Core System Architecture & Modules</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
          <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-1.5">
            <div className="font-semibold text-slate-200 flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-blue-400" />
              <span>Criminal Knowledge Graph (CKG)</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              117,000+ records ingested across Persons, Accounts, Phones, Organizations, Vehicles, and Events. Every edge strictly enforces the Tri-Partite taxonomy (Explicit / Inferred / Predicted).
            </p>
          </div>

          <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-1.5">
            <div className="font-semibold text-slate-200 flex items-center gap-1.5">
              <Workflow className="w-3.5 h-3.5 text-emerald-400" />
              <span>Multilingual Entity Resolution</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              Resolves Hindi / Devanagari variants (e.g. <code>राहुल जोशी</code> ➔ <code>Rahul Joshi / P00231</code>), initials (<code>R. Joshi</code>), and optical character recognition (OCR) noise with 94%+ match precision.
            </p>
          </div>

          <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-1.5">
            <div className="font-semibold text-slate-200 flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-amber-400" />
              <span>Multi-Tier Anomaly Engine</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              Combines Tier 1 typology rules (Mule fan-in, smurfing, scatter-gather) with Tier 2 OddBall structural power-law anomaly detection and Tier 3 temporal burst Z-score analytics.
            </p>
          </div>

          <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg space-y-1.5">
            <div className="font-semibold text-slate-200 flex items-center gap-1.5">
              <Scale className="w-3.5 h-3.5 text-rose-400" />
              <span>Section 63 BSA Digital Custody</span>
            </div>
            <p className="text-slate-400 leading-relaxed">
              Every lead dossier is bound to its source evidence IDs and cryptographically sealed with a SHA-256 hash to satisfy Indian Evidence Act / Section 63 BSA electronic admissibility.
            </p>
          </div>
        </div>
      </div>

      {/* Governing Legal Mandate */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-2">
        <div className="flex items-center gap-2 text-xs font-bold text-amber-400 uppercase tracking-wider">
          <Scale className="w-4 h-4" />
          <span>Governing Legal Principle: Leads, Not Proof</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          ORION is an <strong>investigative intelligence decision-support platform</strong>. It identifies hidden links, calculates risk probabilities, and formulates prioritized statutory recommendations (e.g. Section 102 Cr.P.C. account freezes, Section 91 Cr.P.C. requisition notices). It does not pass judicial verdicts; all leads require corroborative inquiry by the designated investigating officer.
        </p>
      </div>

    </div>
  );
}
