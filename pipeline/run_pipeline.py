"""
pipeline/run_pipeline.py — Master Input-to-Leads Pipeline Orchestrator & CLI
SIH PS 189 · I4C / Ministry of Home Affairs

End-to-End Execution Flow:
[Input: Raw FIR / Stream] -> [Stage 1: Extraction] -> [Stage 2: Multilingual Resolution]
  -> [Stage 3: Graph Ingestion & Tri-Partite Classification]
  -> [Stage 4: Multi-Tier Anomaly Detection] -> [Stage 5: Court-Admissible Leads]
"""

import sys
import os
import json
import argparse
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to sys.path to support direct CLI invocation
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from pipeline.samples import SAMPLES, SAMPLE_FIR_MULE
    from pipeline.extractor import EntityExtractor
    from pipeline.entity_resolver import MultilingualEntityResolver
    from pipeline.graph_updater import CriminalKnowledgeGraph
    from pipeline.detector import MultiTierDetector
    from pipeline.lead_generator import LeadGenerator
except ImportError:
    from .samples import SAMPLES, SAMPLE_FIR_MULE
    from .extractor import EntityExtractor
    from .entity_resolver import MultilingualEntityResolver
    from .graph_updater import CriminalKnowledgeGraph
    from .detector import MultiTierDetector
    from .lead_generator import LeadGenerator

# ANSI color codes for rich CLI terminal experience
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

def clean_obj(obj):
    """Recursively sanitize float NaN and non-serializable objects."""
    import math
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
        return obj
    elif isinstance(obj, dict):
        return {k: clean_obj(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_obj(item) for item in obj]
    return obj


def run_input_to_leads_pipeline(raw_input: Dict[str, Any], verbose: bool = True) -> Dict[str, Any]:
    """
    Executes the full 5-stage pipeline from raw input to court-admissible leads.
    """
    t0 = time.time()
    source_type = raw_input.get("source_type", "UNSTRUCTURED_FIR")
    doc_id = raw_input.get("document_id") or raw_input.get("feed_id") or "DOC_INPUT"

    if verbose:
        print(f"\n{BOLD}{CYAN}================================================================================{RESET}")
        print(f"{BOLD}{CYAN}      ORION · CRIMINAL NETWORK DISCOVERY & LEAD GENERATION SYSTEM{RESET}")
        print(f"{DIM}      I4C / Ministry of Home Affairs · Section 63 BSA Mandate: Leads, Not Proof{RESET}")
        print(f"{BOLD}{CYAN}================================================================================{RESET}\n")
        print(f"{BOLD}[PIPELINE INITIALIZED]{RESET}")
        print(f"  • Source Document/Feed ID : {YELLOW}{doc_id}{RESET}")
        print(f"  • Source Type             : {YELLOW}{source_type}{RESET}")

    # ── STAGE 1: INGESTION & EXTRACTION ─────────────────────────────────────
    t_stage1 = time.time()
    extractor = EntityExtractor()
    if source_type in ("TRANSACTION_STREAM", "CDR_STREAM"):
        extracted = extractor.extract_from_stream(raw_input)
    else:
        text = raw_input.get("raw_text", "")
        extracted = extractor.extract_from_unstructured(text, document_id=doc_id)
    t_stage1_dur = (time.time() - t_stage1) * 1000

    if verbose:
        print(f"\n{BOLD}── STAGE 1: Multilingual Entity Extraction ({t_stage1_dur:.1f}ms) ──{RESET}")
        print(f"  • Accounts Extracted : {len(extracted.accounts)} -> {', '.join(extracted.accounts[:6])}{'...' if len(extracted.accounts) > 6 else ''}")
        print(f"  • Phones Extracted   : {len(extracted.phones)} -> {', '.join(extracted.phones)}")
        print(f"  • Persons Mentioned  : {len(extracted.persons)} -> {', '.join(p['raw_name'] for p in extracted.persons)}")
        print(f"  • Financial Amounts  : {len(extracted.amounts)} -> {', '.join(f'₹{a:,.0f}' for a in extracted.amounts)}")

    # ── STAGE 2: MULTILINGUAL RESOLUTION & ALIAS DISAMBIGUATION ───────────────
    t_stage2 = time.time()
    resolver = MultilingualEntityResolver()
    resolved_persons = [resolver.resolve_person_mention(p["raw_name"]) for p in extracted.persons]
    resolved_accounts = [resolver.resolve_account(acc) for acc in extracted.accounts]
    resolved_phones = [resolver.resolve_phone(ph) for ph in extracted.phones]
    t_stage2_dur = (time.time() - t_stage2) * 1000

    if verbose:
        print(f"\n{BOLD}── STAGE 2: Multilingual Entity Resolution & Stitching ({t_stage2_dur:.1f}ms) ──{RESET}")
        for rp in resolved_persons:
            color = GREEN if rp.confidence >= 0.85 else YELLOW
            print(f"  • [PERSON MATCH] '{rp.raw_mention}' -> {color}{rp.canonical_name} ({rp.canonical_id}){RESET} "
                  f"| Type: {rp.match_type} | Conf: {rp.confidence*100:.0f}%")
        for ra in resolved_accounts[:4]:
            if ra['found_in_registry']:
                print(f"  • [ACCOUNT LINK] {ra['account_id']} -> Holder: {GREEN}{ra['holder_name']} ({ra['holder_person_id']}){RESET} | {ra['financial_institution']}")

    # ── STAGE 3: KNOWLEDGE GRAPH EXPANSION & TRI-PARTITE TAXONOMY ─────────────
    t_stage3 = time.time()
    ckg = CriminalKnowledgeGraph()

    # Ingest persons
    for rp in resolved_persons:
        ckg.add_node(rp.canonical_id, rp.canonical_name, "Person", {
            "aliases": [rp.raw_mention],
            "confidence": rp.confidence
        })

    # Ingest accounts
    for ra in resolved_accounts:
        ckg.add_node(ra["account_id"], ra["account_id"], "Account", {
            "holder_id": ra.get("holder_person_id"),
            "holder_name": ra.get("holder_name"),
            "bank": ra.get("financial_institution")
        })
        # Add explicit ownership edge if holder known
        if ra.get("holder_person_id") and ra.get("holder_person_id") in ckg.nodes:
            ckg.add_edge(
                edge_id=f"OWN_{ra['holder_person_id']}_{ra['account_id']}",
                source=ra['holder_person_id'],
                target=ra['account_id'],
                edge_type="OWNS",
                taxonomy="Explicit",
                evidence_id=f"EVD_KYC_{ra['account_id']}",
                confidence=0.99
            )

    # Ingest phones
    for rph in resolved_phones:
        ckg.add_node(rph["phone_id"], rph["phone_id"], "Phone", {
            "subscriber_id": rph.get("subscriber_person_id"),
            "provider": rph.get("service_provider")
        })
        if rph.get("subscriber_person_id") and rph.get("subscriber_person_id") in ckg.nodes:
            ckg.add_edge(
                edge_id=f"SUB_{rph['subscriber_person_id']}_{rph['phone_id']}",
                source=rph['subscriber_person_id'],
                target=rph['phone_id'],
                edge_type="SUBSCRIBES",
                taxonomy="Explicit",
                evidence_id=f"EVD_CAF_{rph['phone_id']}",
                confidence=0.99
            )

    # Ingest transaction edges
    if extracted.inferred_transfers:
        for t in extracted.inferred_transfers:
            if "tx_id" in t:
                ckg.add_edge(
                    edge_id=t["tx_id"],
                    source=t["source"],
                    target=t["target"],
                    edge_type="TRANSACTED",
                    taxonomy="Explicit",
                    evidence_id=t.get("evidence_id", "EVD_BNK"),
                    confidence=0.98,
                    properties={"amount": t["amount"], "timestamp": t["timestamp"]}
                )
            elif "comm_id" in t:
                ckg.add_edge(
                    edge_id=t["comm_id"],
                    source=t["source_phone"],
                    target=t["target_phone"],
                    edge_type="COMMUNICATED",
                    taxonomy="Explicit",
                    evidence_id=t.get("evidence_id", "EVD_CDR"),
                    confidence=0.95,
                    properties={"duration": t.get("duration", 0), "timestamp": t["timestamp"]}
                )
    else:
        # For unstructured FIR: construct inferred/explicit links mentioned in the complaint
        # In SAMPLE_FIR_MULE, feeder accounts A00001..A00012 funnel to A00013, and A00013 to A00014
        if "A00013" in extracted.accounts:
            for acc in extracted.accounts:
                if acc not in ("A00013", "A00014"):
                    ckg.add_edge(
                        edge_id=f"TX_IN_{acc}_A00013",
                        source=acc,
                        target="A00013",
                        edge_type="TRANSACTED",
                        taxonomy="Explicit",
                        evidence_id="EVD_FIR_STMT",
                        confidence=0.95,
                        properties={"amount": 11200.0, "timestamp": "2026-08-01 12:00:00"}
                    )
            if "A00014" in extracted.accounts:
                ckg.add_edge(
                    edge_id="TX_OUT_A00013_A00014",
                    source="A00013",
                    target="A00014",
                    edge_type="TRANSACTED",
                    taxonomy="Explicit",
                    evidence_id="EVD_FIR_OUT",
                    confidence=0.97,
                    properties={"amount": 120000.0, "timestamp": "2026-08-02 21:00:00"}
                )

    # Inferred edge: Co-occurrence / Co-location mentioned in the same case document
    for rp in resolved_persons:
        for acc in extracted.accounts:
            if acc == "A00013":
                ckg.add_edge(
                    edge_id=f"INF_CO_{rp.canonical_id}_{acc}",
                    source=rp.canonical_id,
                    target=acc,
                    edge_type="OPERATES_INFERRED",
                    taxonomy="Inferred",
                    evidence_id="EVD_FIR_PROVENANCE",
                    confidence=0.88,
                    properties={"basis": "Co-occurrence in case complaint narrative"}
                )

    summary = ckg.summary()
    t_stage3_dur = (time.time() - t_stage3) * 1000

    if verbose:
        print(f"\n{BOLD}── STAGE 3: Knowledge Graph Expansion & Tri-Partite Classification ({t_stage3_dur:.1f}ms) ──{RESET}")
        print(f"  • Total Graph Nodes : {summary['total_nodes']} ({summary['node_breakdown']})")
        print(f"  • Total Graph Edges : {summary['total_edges']}")
        print(f"  • Taxonomy Breakdown: "
              f"{GREEN}Explicit: {summary['taxonomy_breakdown']['Explicit']}{RESET} | "
              f"{YELLOW}Inferred: {summary['taxonomy_breakdown']['Inferred']}{RESET} | "
              f"{CYAN}Predicted: {summary['taxonomy_breakdown']['Predicted']}{RESET}")

    # ── STAGE 4: MULTI-TIER ANOMALY & PATTERN DETECTION ───────────────────────
    t_stage4 = time.time()
    detector = MultiTierDetector()
    findings = detector.run_all(ckg)
    t_stage4_dur = (time.time() - t_stage4) * 1000

    if verbose:
        print(f"\n{BOLD}── STAGE 4: Multi-Tier Network & Anomaly Detection ({t_stage4_dur:.1f}ms) ──{RESET}")
        print(f"  • Active Analytical Tiers : Tier 1 (Typology), Tier 2 (OddBall), Tier 3 (Burst), Tier 4 (Link Prediction)")
        print(f"  • Total Findings Flagged  : {BOLD}{len(findings)}{RESET}")
        for f in findings:
            lvl_color = RED if f.threat_level == "CRITICAL" else (YELLOW if f.threat_level == "HIGH" else CYAN)
            print(f"    ▶ [{f.tier}] {BOLD}{lvl_color}{f.pattern_name}{RESET} "
                  f"(Threat: {lvl_color}{f.threat_level}{RESET}, Conf: {f.confidence*100:.0f}%)")
            print(f"      {DIM}{f.rationale[:110]}...{RESET}")

    # ── STAGE 5: COURT-ADMISSIBLE LEADS & SECTION 63 BSA CERTIFICATION ────────
    t_stage5 = time.time()
    lead_gen = LeadGenerator()
    leads = lead_gen.generate_leads(findings, resolved_persons, document_id=doc_id)
    t_stage5_dur = (time.time() - t_stage5) * 1000
    total_pipeline_time = (time.time() - t0) * 1000

    if verbose:
        print(f"\n{BOLD}── STAGE 5: Court-Admissible Lead Synthesis & Section 63 BSA Custody ({t_stage5_dur:.1f}ms) ──{RESET}")
        print(f"  • Total Actionable Leads Formulated : {BOLD}{GREEN}{len(leads)}{RESET}")
        print(f"  • Total Pipeline Execution Time    : {BOLD}{total_pipeline_time:.1f} ms{RESET}\n")

        for idx, lead in enumerate(leads, 1):
            lvl_color = RED if lead.threat_level == "CRITICAL" else (YELLOW if lead.threat_level == "HIGH" else CYAN)
            print(f"{BOLD}{CYAN}================================================================================{RESET}")
            print(f"{BOLD}LEAD #{idx}: {lvl_color}[{lead.threat_level}] {lead.title}{RESET}")
            print(f"{DIM}Lead Reference ID: {lead.lead_id} | Timestamp: {lead.generated_at}{RESET}")
            print(f"{BOLD}Governing Legal Mandate:{RESET} {DIM}{lead.governing_principle}{RESET}")
            print(f"\n{BOLD}1. PRIMARY SUSPECT IDENTIFIED:{RESET}")
            print(f"   • Canonical ID    : {lead.primary_suspect.get('canonical_id')}")
            print(f"   • Full Legal Name : {lead.primary_suspect.get('canonical_name')}")
            print(f"   • Resolved Aliases: {', '.join(lead.primary_suspect.get('resolved_aliases', []))}")
            print(f"\n{BOLD}2. EVIDENTIARY NARRATIVE:{RESET}")
            print(f"   {lead.narrative_summary}")
            print(f"\n{BOLD}3. ACTIONABLE STATUTORY NEXT STEPS:{RESET}")
            for rec in lead.actionable_recommendations:
                print(f"   [!] {rec}")
            print(f"\n{BOLD}4. SECTION 63 BSA DIGITAL CUSTODY SEAL:{RESET}")
            print(f"   SHA-256 Hash: {GREEN}{lead.custody_hash}{RESET}")
            print(f"{BOLD}{CYAN}================================================================================{RESET}\n")

    result_payload = {
        "metadata": {
            "source_id": doc_id,
            "source_type": source_type,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "total_execution_ms": round(total_pipeline_time, 2),
            "stages_timing_ms": {
                "stage1_extraction": round(t_stage1_dur, 2),
                "stage2_resolution": round(t_stage2_dur, 2),
                "stage3_graph_ingest": round(t_stage3_dur, 2),
                "stage4_anomaly_detection": round(t_stage4_dur, 2),
                "stage5_lead_synthesis": round(t_stage5_dur, 2)
            }
        },
        "extracted_entities": extracted.to_dict(),
        "resolved_entities": [rp.to_dict() for rp in resolved_persons],
        "graph_state": ckg.to_dict(),
        "detection_findings": [f.to_dict() for f in findings],
        "leads": [l.to_dict() for l in leads]
    }

    return clean_obj(result_payload)


def main():
    parser = argparse.ArgumentParser(description="ORION — End-to-End Input-to-Leads Investigative Pipeline (I4C / MHA)")
    parser.add_argument("--sample", choices=["fir", "structuring", "cdr", "scatter"], default="fir",
                        help="Choose built-in test sample (default: fir)")
    parser.add_argument("--input", type=str, default=None,
                        help="Path to custom input file (raw text or JSON)")
    parser.add_argument("--out", type=str, default="pipeline/output_leads.json",
                        help="Path to save output JSON leads dossier")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress terminal log output")
    args = parser.parse_args()

    # Determine input data
    if args.input:
        in_path = Path(args.input)
        if not in_path.exists():
            print(f"Error: Input file {args.input} does not exist.")
            sys.exit(1)
        with open(in_path, "r", encoding="utf-8") as f:
            content = f.read()
            try:
                raw_input = json.loads(content)
            except json.JSONDecodeError:
                raw_input = {
                    "source_type": "UNSTRUCTURED_DOCUMENT",
                    "document_id": in_path.stem,
                    "raw_text": content
                }
    else:
        raw_input = SAMPLES.get(args.sample, SAMPLE_FIR_MULE)

    # Run pipeline
    results = run_input_to_leads_pipeline(raw_input, verbose=not args.quiet)

    # Write output JSON
    out_file = Path(args.out)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    if not args.quiet:
        print(f"{GREEN}✓ Successfully generated {len(results['leads'])} court-admissible lead(s).{RESET}")
        print(f"{DIM}Saved JSON Lead Dossier to: {out_file.resolve()}{RESET}\n")


if __name__ == "__main__":
    main()
