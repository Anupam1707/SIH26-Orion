"""
pipeline/extractor.py — Multilingual Entity & Flow Extractor
SIH PS 189 · I4C / Ministry of Home Affairs

Extracts raw entities, financial amounts, timestamps, and relationship indicators
from unstructured documents (FIRs, field reports) and structured data streams (transactions, CDRs).
"""

import re
from typing import Dict, List, Any, Optional

class RawEntityExtraction:
    def __init__(self):
        self.persons: List[Dict[str, Any]] = []
        self.accounts: List[str] = []
        self.phones: List[str] = []
        self.vehicles: List[str] = []
        self.amounts: List[float] = []
        self.timestamps: List[str] = []
        self.inferred_transfers: List[Dict[str, Any]] = []
        self.raw_mentions: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "persons": self.persons,
            "accounts": list(dict.fromkeys(self.accounts)),
            "phones": list(dict.fromkeys(self.phones)),
            "vehicles": list(dict.fromkeys(self.vehicles)),
            "amounts": self.amounts,
            "timestamps": list(dict.fromkeys(self.timestamps)),
            "inferred_transfers": self.inferred_transfers,
            "raw_mentions_count": len(self.raw_mentions)
        }


class EntityExtractor:
    """
    Parses unstructured text and structured feeds into normalized entity candidates.
    Supports English, Devanagari script, and hybrid mixed-language inputs.
    """

    # Regex patterns
    ACCOUNT_REGEX = re.compile(r'\b(A\d{5})\b', re.IGNORECASE)
    PHONE_REGEX = re.compile(r'\b(PH\d{5})\b', re.IGNORECASE)
    VEHICLE_REGEX = re.compile(r'\b([A-Z]{2}\d{2}[A-Z]{1,2}\d{4})\b')
    AMOUNT_REGEX = re.compile(r'(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d{1,2})?)', re.IGNORECASE)
    DATE_REGEX = re.compile(r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}(?:\s+\d{2}:\d{2}(?::\d{2})?)?)\b')
    
    # Devanagari character block: \u0900-\u097F
    DEVANAGARI_NAME_REGEX = re.compile(r'[\u0900-\u097F]+(?:\s+[\u0900-\u097F]+)+')

    # Common English full-name pattern in legal texts (Capitalized Two/Three-word tokens)
    ENGLISH_NAME_REGEX = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z]\.?|\s+[A-Z][a-z]+)+)\b')

    # Stop words to exclude from English name matches
    NAME_STOPWORDS = {
        "First Information", "Information Report", "Cyber Crime", "Police Station", 
        "Central District", "Date Time", "Complaint Narrative", "National Payment",
        "Payment Corp", "State Bank", "Central Business", "Business District",
        "Business Area", "Synthetic Investigative", "Investigative Records", "Field Officer",
        "Investigating Officer", "Public Sector", "Commercial Bank", "Section Cr",
        "Downstream Exit"
    }

    def __init__(self):
        pass

    def extract_from_unstructured(self, text: str, document_id: str = "DOC_RAW") -> RawEntityExtraction:
        result = RawEntityExtraction()

        # 1. Accounts
        for match in self.ACCOUNT_REGEX.finditer(text):
            acc_id = match.group(1).upper()
            result.accounts.append(acc_id)
            result.raw_mentions.append(acc_id)

        # 2. Phone numbers
        for match in self.PHONE_REGEX.finditer(text):
            phone_id = match.group(1).upper()
            result.phones.append(phone_id)
            result.raw_mentions.append(phone_id)

        # 3. Vehicles
        for match in self.VEHICLE_REGEX.finditer(text):
            veh = match.group(1).upper()
            result.vehicles.append(veh)
            result.raw_mentions.append(veh)

        # 4. Currency amounts
        for match in self.AMOUNT_REGEX.finditer(text):
            val_str = match.group(1).replace(',', '')
            try:
                result.amounts.append(float(val_str))
            except ValueError:
                pass

        # 5. Timestamps / Dates
        for match in self.DATE_REGEX.finditer(text):
            result.timestamps.append(match.group(1))

        # 6. Devanagari Names
        for match in self.DEVANAGARI_NAME_REGEX.finditer(text):
            dev_name = match.group(0).strip()
            result.persons.append({
                "raw_name": dev_name,
                "script": "Devanagari",
                "document_id": document_id
            })
            result.raw_mentions.append(dev_name)

        # 7. English Names
        for match in self.ENGLISH_NAME_REGEX.finditer(text):
            eng_name = match.group(1).strip()
            if eng_name not in self.NAME_STOPWORDS and len(eng_name.split()) >= 2:
                # Avoid duplicates
                if not any(p["raw_name"] == eng_name for p in result.persons):
                    result.persons.append({
                        "raw_name": eng_name,
                        "script": "Latin",
                        "document_id": document_id
                    })
                    result.raw_mentions.append(eng_name)

        return result

    def extract_from_stream(self, data: Dict[str, Any]) -> RawEntityExtraction:
        result = RawEntityExtraction()
        source_type = data.get("source_type", "")

        if source_type == "TRANSACTION_STREAM":
            records = data.get("records", [])
            for r in records:
                src = r.get("source_account_id")
                tgt = r.get("target_account_id")
                amt = float(r.get("amount", 0.0))
                ts = r.get("timestamp")
                if src:
                    result.accounts.append(src)
                if tgt:
                    result.accounts.append(tgt)
                if amt > 0:
                    result.amounts.append(amt)
                if ts:
                    result.timestamps.append(ts)
                result.inferred_transfers.append({
                    "tx_id": r.get("transaction_id"),
                    "source": src,
                    "target": tgt,
                    "amount": amt,
                    "timestamp": ts,
                    "channel": r.get("channel", "BANK"),
                    "evidence_id": r.get("evidence_id", "EVD_STREAM")
                })

        elif source_type == "CDR_STREAM":
            records = data.get("records", [])
            for r in records:
                src = r.get("source_phone_id")
                tgt = r.get("target_phone_id")
                ts = r.get("timestamp")
                if src:
                    result.phones.append(src)
                if tgt:
                    result.phones.append(tgt)
                if ts:
                    result.timestamps.append(ts)
                result.inferred_transfers.append({
                    "comm_id": r.get("communication_id"),
                    "source_phone": src,
                    "target_phone": tgt,
                    "timestamp": ts,
                    "duration": r.get("duration_seconds", 0),
                    "evidence_id": r.get("evidence_id", "EVD_CDR")
                })

        return result
