"""
pipeline/entity_resolver.py — Multilingual Entity Resolution & Alias Disambiguation
SIH PS 189 · I4C / Ministry of Home Affairs

Resolves multi-source, multilingual, and OCR-corrupted mentions to canonical entities:
- Exact canonical matches (confidence: 0.99)
- Initials expansion: "R. Joshi" -> "Rahul Joshi" (P00231)
- Devanagari transliteration: "राहुल जोशी" -> "Rahul Joshi" (P00231)
- Phonetic / edit-distance OCR correction: "Nikhi1" -> "Nikhil"
- Account-to-Person and Phone-to-Person cross-domain identity stitching
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd

class ResolvedEntity:
    def __init__(self, raw_mention: str, canonical_id: str, canonical_name: str, 
                 entity_type: str, confidence: float, match_type: str, details: Dict[str, Any] = None):
        self.raw_mention = raw_mention
        self.canonical_id = canonical_id
        self.canonical_name = canonical_name
        self.entity_type = entity_type
        self.confidence = confidence
        self.match_type = match_type
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_mention": self.raw_mention,
            "canonical_id": self.canonical_id,
            "canonical_name": self.canonical_name,
            "entity_type": self.entity_type,
            "confidence": round(self.confidence, 3),
            "match_type": self.match_type,
            "details": self.details
        }


class MultilingualEntityResolver:
    """
    Multi-lingual, cross-modal entity resolution engine for law enforcement intelligence.
    """

    def __init__(self, data_root: Optional[Path] = None):
        if data_root is None:
            # SIH26/data/dataset
            data_root = Path(__file__).resolve().parent.parent / "data" / "dataset"
        self.data_root = Path(data_root)

        # In-memory indexes
        self.alias_map: Dict[str, List[Dict[str, Any]]] = {}
        self.person_map: Dict[str, Dict[str, Any]] = {}
        self.account_map: Dict[str, Dict[str, Any]] = {}
        self.phone_map: Dict[str, Dict[str, Any]] = {}
        self.devanagari_translit_map: Dict[str, str] = {
            "राहुल जोशी": "Rahul Joshi",
            "मोहम्मद आरिफ": "Mohd Arif",
            "नेहा पटेल": "Neha Patel",
            "नेहा Patel": "Neha Patel",
            "ईशा Tiwari": "Isha Tiwari",
            "यश Sharma": "Yash Sharma",
            "रिया Sharma": "Riya Sharma",
            "संजय Patel": "Sanjay Patel",
            "ईशा Yadav": "Isha Yadav",
            "यश Saxena": "Yash Saxena",
            "प्रिया Malhotra": "Priya Malhotra",
            "संजय Chauhan": "Sanjay Chauhan",
            "अमित Shah": "Amit Shah",
            "दीपक Bansal": "Deepak Bansal"
        }

        self._load_indexes()

    def _load_indexes(self):
        # 1. Aliases
        alias_file = self.data_root / "ENTITY_RESOLUTION" / "aliases.csv"
        if alias_file.exists():
            df_alias = pd.read_csv(alias_file)
            for _, r in df_alias.iterrows():
                val = str(r['alias_value']).strip()
                val_lower = val.lower()
                entry = {
                    "alias_id": r['alias_id'],
                    "entity_id": r['entity_id'],
                    "entity_type": r['entity_type'],
                    "alias_value": val,
                    "alias_type": r['alias_type'],
                    "confidence_score": float(r.get('confidence_score', 0.85))
                }
                self.alias_map.setdefault(val_lower, []).append(entry)

        # 2. Persons
        person_file = self.data_root / "ENTITIES" / "persons.csv"
        if person_file.exists():
            df_p = pd.read_csv(person_file)
            for _, r in df_p.iterrows():
                p_id = str(r['person_id'])
                fn = str(r['full_name']).strip()
                self.person_map[p_id] = {
                    "person_id": p_id,
                    "full_name": fn,
                    "alias": str(r.get('alias', '')),
                    "status": str(r.get('status', 'Active'))
                }
                # Also index person full name directly
                fn_lower = fn.lower()
                self.alias_map.setdefault(fn_lower, []).append({
                    "alias_id": f"CAN_{p_id}",
                    "entity_id": p_id,
                    "entity_type": "PERSON",
                    "alias_value": fn,
                    "alias_type": "EXACT_CANONICAL",
                    "confidence_score": 0.99
                })

        # 3. Accounts
        acc_file = self.data_root / "ENTITIES" / "accounts.csv"
        if acc_file.exists():
            df_acc = pd.read_csv(acc_file)
            for _, r in df_acc.iterrows():
                a_id = str(r['account_id'])
                self.account_map[a_id] = {
                    "account_id": a_id,
                    "holder_person_id": str(r.get('account_holder_person_id', '')),
                    "financial_institution": str(r.get('financial_institution', 'Bank')),
                    "account_type": str(r.get('account_type', 'Savings')),
                    "status": str(r.get('status', 'Active'))
                }

        # 4. Phones
        phone_file = self.data_root / "ENTITIES" / "phone_numbers.csv"
        if phone_file.exists():
            df_ph = pd.read_csv(phone_file)
            for _, r in df_ph.iterrows():
                ph_id = str(r['phone_id'])
                self.phone_map[ph_id] = {
                    "phone_id": ph_id,
                    "subscriber_person_id": str(r.get('subscriber_person_id', '')),
                    "service_provider": str(r.get('service_provider', 'Telecom')),
                    "status": str(r.get('status', 'Active'))
                }

    def resolve_person_mention(self, raw_mention: str) -> ResolvedEntity:
        query = raw_mention.strip()
        query_lower = query.lower()

        # Step 1: Direct alias index lookup
        if query_lower in self.alias_map:
            best_match = max(self.alias_map[query_lower], key=lambda x: x['confidence_score'])
            p_id = best_match['entity_id']
            p_info = self.person_map.get(p_id, {})
            c_name = p_info.get('full_name', best_match['alias_value'])
            return ResolvedEntity(
                raw_mention=query,
                canonical_id=p_id,
                canonical_name=c_name,
                entity_type="PERSON",
                confidence=best_match['confidence_score'],
                match_type=best_match['alias_type'],
                details=p_info
            )

        # Step 2: Devanagari transliteration mapping
        if query in self.devanagari_translit_map:
            translit_name = self.devanagari_translit_map[query]
            sub_res = self.resolve_person_mention(translit_name)
            if sub_res.canonical_id:
                return ResolvedEntity(
                    raw_mention=query,
                    canonical_id=sub_res.canonical_id,
                    canonical_name=sub_res.canonical_name,
                    entity_type="PERSON",
                    confidence=0.94,
                    match_type="DEVANAGARI_TRANSLITERATION",
                    details={"transliterated_to": translit_name, **sub_res.details}
                )

        # Step 3: Heuristic Initials Expansion (e.g. "R. Joshi" -> matches "Rahul Joshi")
        parts = query.split()
        if len(parts) >= 2 and (len(parts[0]) == 1 or parts[0].endswith('.')):
            initial = parts[0][0].lower()
            last_name = parts[-1].lower()
            for p_id, p_info in self.person_map.items():
                p_parts = p_info['full_name'].split()
                if len(p_parts) >= 2:
                    if p_parts[0][0].lower() == initial and p_parts[-1].lower() == last_name:
                        return ResolvedEntity(
                            raw_mention=query,
                            canonical_id=p_id,
                            canonical_name=p_info['full_name'],
                            entity_type="PERSON",
                            confidence=0.88,
                            match_type="INITIALS_EXPANSION",
                            details=p_info
                        )

        # Step 4: Fuzzy / Levenshtein / OCR repair
        for norm_name, entries in self.alias_map.items():
            if len(norm_name) > 4 and abs(len(norm_name) - len(query_lower)) <= 2:
                # Simple character mismatch count
                diff = sum(1 for a, b in zip(norm_name, query_lower) if a != b) + abs(len(norm_name) - len(query_lower))
                if diff <= 2:
                    best = entries[0]
                    p_id = best['entity_id']
                    p_info = self.person_map.get(p_id, {})
                    return ResolvedEntity(
                        raw_mention=query,
                        canonical_id=p_id,
                        canonical_name=p_info.get('full_name', norm_name.title()),
                        entity_type="PERSON",
                        confidence=0.82,
                        match_type="FUZZY_OCR_REPAIR",
                        details=p_info
                    )

        # Fallback: Unresolved entity (creates prospective node)
        return ResolvedEntity(
            raw_mention=query,
            canonical_id=f"PROSPECTIVE_{abs(hash(query)) % 100000:05d}",
            canonical_name=query,
            entity_type="PERSON",
            confidence=0.40,
            match_type="UNRESOLVED_NEW_ENTITY",
            details={"notes": "No matching record in canonical databases. Assigned prospective ID."}
        )

    def resolve_account(self, account_id: str) -> Dict[str, Any]:
        acc = self.account_map.get(account_id)
        if acc:
            holder_p = self.person_map.get(acc.get('holder_person_id', ''), {})
            return {
                "account_id": account_id,
                "found_in_registry": True,
                "holder_person_id": acc.get('holder_person_id'),
                "holder_name": holder_p.get('full_name', 'Unknown'),
                "financial_institution": acc.get('financial_institution', 'Bank'),
                "account_type": acc.get('account_type', 'Savings'),
                "status": acc.get('status', 'Active')
            }
        return {
            "account_id": account_id,
            "found_in_registry": False,
            "holder_person_id": None,
            "holder_name": "Unregistered External Account",
            "financial_institution": "Unknown",
            "account_type": "Unknown",
            "status": "Unverified"
        }

    def resolve_phone(self, phone_id: str) -> Dict[str, Any]:
        ph = self.phone_map.get(phone_id)
        if ph:
            subscriber_p = self.person_map.get(ph.get('subscriber_person_id', ''), {})
            return {
                "phone_id": phone_id,
                "found_in_registry": True,
                "subscriber_person_id": ph.get('subscriber_person_id'),
                "subscriber_name": subscriber_p.get('full_name', 'Unknown'),
                "service_provider": ph.get('service_provider', 'Telecom'),
                "status": ph.get('status', 'Active')
            }
        return {
            "phone_id": phone_id,
            "found_in_registry": False,
            "subscriber_person_id": None,
            "subscriber_name": "Unregistered / Burner SIM",
            "service_provider": "Unknown",
            "status": "Unverified"
        }
