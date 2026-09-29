"""
pipeline/lead_generator.py — Court-Admissible Lead Synthesis & Section 63 BSA Certification
SIH PS 189 · I4C / Ministry of Home Affairs

Transforms multi-tier detection findings into prioritized, explainable, and
legally compliant investigative leads under the governing principle:
"The system produces leads, not proof" (Section 63 Bharatiya Sakshya Adhiniyam, 2023).
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
try:
    from pipeline.detector import DetectionFinding
    from pipeline.entity_resolver import ResolvedEntity
except ImportError:
    from .detector import DetectionFinding
    from .entity_resolver import ResolvedEntity

class InvestigativeLead:
    def __init__(self, lead_id: str, title: str, threat_level: str, confidence: float,
                 governing_principle: str, primary_suspect: Dict[str, Any],
                 involved_entities: List[Dict[str, Any]], detection_tiers: List[str],
                 narrative_summary: str, evidence_subgraph: Dict[str, Any],
                 actionable_recommendations: List[str]):
        self.lead_id = lead_id
        self.generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        self.title = title
        self.threat_level = threat_level
        self.confidence = confidence
        self.governing_principle = governing_principle
        self.primary_suspect = primary_suspect
        self.involved_entities = involved_entities
        self.detection_tiers = detection_tiers
        self.narrative_summary = narrative_summary
        self.evidence_subgraph = evidence_subgraph
        self.actionable_recommendations = actionable_recommendations
        self.custody_hash = self._generate_custody_hash()

    def _generate_custody_hash(self) -> str:
        # Canonical hash over lead fields for Section 63 BSA chain of custody
        hash_payload = {
            "lead_id": self.lead_id,
            "title": self.title,
            "threat_level": self.threat_level,
            "primary_suspect": self.primary_suspect.get("canonical_id", ""),
            "narrative_summary": self.narrative_summary,
            "evidence_nodes_count": len(self.evidence_subgraph.get("nodes", [])),
            "evidence_edges_count": len(self.evidence_subgraph.get("edges", []))
        }
        raw_bytes = json.dumps(hash_payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw_bytes).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lead_id": self.lead_id,
            "generated_at": self.generated_at,
            "title": self.title,
            "threat_level": self.threat_level,
            "confidence": round(self.confidence, 3),
            "governing_principle": self.governing_principle,
            "primary_suspect": self.primary_suspect,
            "involved_entities": self.involved_entities,
            "detection_tiers": self.detection_tiers,
            "narrative_summary": self.narrative_summary,
            "evidence_subgraph": self.evidence_subgraph,
            "actionable_recommendations": self.actionable_recommendations,
            "section_63_bsa_custody_hash": self.custody_hash,
            "legal_status": "INVESTIGATIVE_LEAD_ONLY_NOT_PROOF"
        }


class LeadGenerator:
    """
    Synthesizes multi-source findings into courtroom-compliant Section 63 BSA investigative leads.
    """

    GOVERNING_PRINCIPLE = (
        "LEADS, NOT PROOF: This automated output is an investigative intelligence lead generated "
        "under Section 63 of the Bharatiya Sakshya Adhiniyam (BSA), 2023. It assists human investigators "
        "in identifying suspicious patterns, freezing proceeds of crime, and issuing statutory notices. "
        "It does not constitute conclusive legal evidence of guilt without independent corroboration."
    )

    def __init__(self):
        pass

    def generate_leads(self, findings: List[DetectionFinding], 
                       resolved_entities: List[ResolvedEntity],
                       document_id: str = "DOC_INPUT") -> List[InvestigativeLead]:
        leads = []
        if not findings:
            return leads

        # Map canonical ID to resolved entity info
        entity_lookup = {r.canonical_id: r.to_dict() for r in resolved_entities}
        primary_person = None
        for r in resolved_entities:
            if r.entity_type == "PERSON" and not r.canonical_id.startswith("PROSPECTIVE"):
                primary_person = r
                break
        if not primary_person and resolved_entities:
            primary_person = resolved_entities[0]

        lead_idx = 1
        for f in findings:
            lead_id = f"LEAD-2026-{document_id.split('-')[-1]}-{lead_idx:02d}"
            lead_idx += 1

            # Format primary suspect block
            suspect_info = {
                "canonical_id": primary_person.canonical_id if primary_person else "UNIDENTIFIED",
                "canonical_name": primary_person.canonical_name if primary_person else "Unidentified Suspect",
                "resolved_aliases": [primary_person.raw_mention] if primary_person else [],
                "match_confidence": primary_person.confidence if primary_person else 0.50
            }

            # Formulate recommendations based on pattern
            recommendations = []
            if "MULE" in f.pattern_name:
                collector = f.focal_entities[0] if f.focal_entities else "Beneficiary Account"
                recommendations.append(
                    f"Immediate lien marking / debit freeze under Section 102 Cr.P.C. on beneficiary collector account {collector}."
                )
                recommendations.append(
                    f"Issue Section 91 Cr.P.C. requisition to the custodian bank for account opening forms (AOF), KYC, and ATM withdrawal logs."
                )
                recommendations.append(
                    "Initiate Section 91 Cr.P.C. notice to telecom service providers for subscriber identity and CDR tower dumps."
                )
                recommendations.append(
                    f"Flag primary suspect {suspect_info['canonical_name']} ({suspect_info['canonical_id']}) in National Cybercrime Reporting Portal (NCRP)."
                )
            elif "STRUCTURING" in f.pattern_name:
                recommendations.append(
                    "Issue immediate CTR/STR inquiry to the Financial Intelligence Unit (FIU-IND) regarding sub-threshold smurfing transactions."
                )
                recommendations.append(
                    "Requisition originating IP addresses and device MAC addresses from Unified Payments Interface (UPI) switch providers."
                )
                recommendations.append(
                    "Trace beneficial ownership of sender accounts under Section 50 of the Prevention of Money Laundering Act (PMLA)."
                )
            elif "SCATTER" in f.pattern_name:
                recommendations.append(
                    "Submit urgent multi-bank freeze requests across all intermediate layering accounts to arrest dissipation of stolen funds."
                )
                recommendations.append(
                    "Requisition high-speed RTGS/NEFT transaction logs from Reserve Bank of India settlement switch."
                )
            elif "BURST" in f.pattern_name:
                recommendations.append(
                    "Requisition Cell Tower Dumps (B-Party & A-Party) for the 48-hour incident window from Circle DoT LSA."
                )
                recommendations.append(
                    "Cross-reference IMEI signatures against Central Equipment Identity Register (CEIR) for cloned or burner hardware."
                )
            else:
                recommendations.append(
                    "Conduct field inquiry and subpoena registered account holders for Section 161 Cr.P.C. examination."
                )
                recommendations.append(
                    "Inspect inter-account fund flows on Indian Cyber Crime Coordination Centre (I4C) coordination platform."
                )

            lead = InvestigativeLead(
                lead_id=lead_id,
                title=f"{f.pattern_name.replace('_', ' ').title()}: {f.threat_level} Threat Detected",
                threat_level=f.threat_level,
                confidence=f.confidence,
                governing_principle=self.GOVERNING_PRINCIPLE,
                primary_suspect=suspect_info,
                involved_entities=[{"id": e} for e in f.focal_entities],
                detection_tiers=[f.tier],
                narrative_summary=f.rationale,
                evidence_subgraph=f.evidence_subgraph,
                actionable_recommendations=recommendations
            )
            leads.append(lead)

        return leads
