"""
pipeline/samples.py — Realistic Multi-Source Sample Inputs for SIH PS 189
SIH PS 189 · I4C / Ministry of Home Affairs

Provides authentic multi-source raw test samples:
1. SAMPLE_FIR_MULE: Unstructured cyber-crime police FIR (English with Devanagari suspect name, accounts, dates).
2. SAMPLE_TRANSACTIONS_STRUCTURING: Batch of financial transactions exhibiting smurfing below regulatory threshold.
3. SAMPLE_CDR_BURST: Telecommunications CDR stream showing pre-incident communication burst.
4. SAMPLE_SCATTER_GATHER: High-velocity scatter-gather transaction sequence.
"""

SAMPLE_FIR_MULE = {
    "source_type": "UNSTRUCTURED_FIR",
    "document_id": "FIR-2026-CYBER-0881",
    "police_station": "Cyber Crime Police Station, Central District, New Delhi",
    "date_of_complaint": "2026-08-03",
    "complainant": "Shri Arvind Swaminathan, AGM Fraud Risk, National Payment Corp",
    "raw_text": """
FIRST INFORMATION REPORT (Under Section 154 Cr.P.C.)
Cyber Crime Police Station, Central District | Case Ref: FIR-2026-CYBER-0881
Date & Time of Report: 03-08-2026 10:15 IST

COMPLAINT NARRATIVE:
On 02-08-2026, automated fraud monitoring systems detected an anomalous multi-source fund convergence
syndicate. Between 01-08-2026 09:00 IST and 02-08-2026 21:00 IST, twelve disparate source bank accounts
(identified as feeder accounts A00001, A00002, A00003, A00004, A00005, A00006, A00007, A00008, A00009,
A00010, A00011, and A00012) initiated rapid successive transfers totaling ₹1,34,500 via IMPS, UPI, and RTGS.

All funds were funneled into a central beneficiary collection account A00013 maintained at State Bank of India.
Upon receipt of the aggregated sum, primary account holder Rahul Joshi (also documented in state records as
राहुल जोशी and R. Joshi, Person ID P00231) immediately executed a high-velocity outward transfer of ₹1,20,000
to downstream exit/cashout account A00014 held in the name of Pooja Shah (P00771).

The suspect Rahul Joshi was tracked communicating via mobile number PH04296 and utilizing vehicle DL88JK4478
near Central Business District. A total sum of ₹1,34,500 has been diverted through this mule conduit within 36 hours.
Urgent investigation, freezing of proceeds of crime, and intelligence network tracing is requested.
"""
}

SAMPLE_TRANSACTIONS_STRUCTURING = {
    "source_type": "TRANSACTION_STREAM",
    "feed_id": "STREAM-STR-2026-0828",
    "financial_institution": "Multiple Scheduled Commercial Banks",
    "time_window": "2026-08-28 08:00:00 to 2026-08-28 18:00:00",
    "records": [
        {"transaction_id": "TX_STR_001", "source_account_id": "A00069", "target_account_id": "A00070", "amount": 9200.0, "currency": "INR", "timestamp": "2026-08-28 08:15:22", "channel": "UPI", "evidence_id": "EVD_BNK_901"},
        {"transaction_id": "TX_STR_002", "source_account_id": "A00069", "target_account_id": "A00071", "amount": 9500.0, "currency": "INR", "timestamp": "2026-08-28 09:30:10", "channel": "IMPS", "evidence_id": "EVD_BNK_902"},
        {"transaction_id": "TX_STR_003", "source_account_id": "A00070", "target_account_id": "A00072", "amount": 9800.0, "currency": "INR", "timestamp": "2026-08-28 11:05:45", "channel": "NEFT", "evidence_id": "EVD_BNK_903"},
        {"transaction_id": "TX_STR_004", "source_account_id": "A00071", "target_account_id": "A00073", "amount": 9400.0, "currency": "INR", "timestamp": "2026-08-28 13:40:19", "channel": "UPI", "evidence_id": "EVD_BNK_904"},
        {"transaction_id": "TX_STR_005", "source_account_id": "A00072", "target_account_id": "A00074", "amount": 9900.0, "currency": "INR", "timestamp": "2026-08-28 15:20:00", "channel": "RTGS", "evidence_id": "EVD_BNK_905"},
        {"transaction_id": "TX_STR_006", "source_account_id": "A00073", "target_account_id": "A00074", "amount": 9650.0, "currency": "INR", "timestamp": "2026-08-28 17:45:12", "channel": "IMPS", "evidence_id": "EVD_BNK_906"}
    ]
}

SAMPLE_CDR_BURST = {
    "source_type": "CDR_STREAM",
    "feed_id": "CDR-BURST-2026-0606",
    "telecom_circle": "Delhi-NCR Circle",
    "time_window": "2026-06-06 19:21:33 to 2026-06-08 19:21:33",
    "records": [
        {"communication_id": "CDR_BST_01", "source_phone_id": "PH04296", "target_phone_id": "PH02372", "timestamp": "2026-06-06 20:21:33", "duration_seconds": 184, "cell_tower_source": "TWR_DEL_401", "cell_tower_target": "TWR_DEL_812", "evidence_id": "EVPBU00101"},
        {"communication_id": "CDR_BST_02", "source_phone_id": "PH04296", "target_phone_id": "PH04186", "timestamp": "2026-06-06 21:05:12", "duration_seconds": 92, "cell_tower_source": "TWR_DEL_401", "cell_tower_target": "TWR_NOI_205", "evidence_id": "EVPBU00102"},
        {"communication_id": "CDR_BST_03", "source_phone_id": "PH02372", "target_phone_id": "PH01792", "timestamp": "2026-06-06 22:40:05", "duration_seconds": 310, "cell_tower_source": "TWR_DEL_812", "cell_tower_target": "TWR_DEL_330", "evidence_id": "EVPBU00103"},
        {"communication_id": "CDR_BST_04", "source_phone_id": "PH04186", "target_phone_id": "PH04027", "timestamp": "2026-06-07 01:15:40", "duration_seconds": 45, "cell_tower_source": "TWR_NOI_205", "cell_tower_target": "TWR_GUR_114", "evidence_id": "EVPBU00104"},
        {"communication_id": "CDR_BST_05", "source_phone_id": "PH04296", "target_phone_id": "PH02598", "timestamp": "2026-06-07 03:50:22", "duration_seconds": 215, "cell_tower_source": "TWR_DEL_401", "cell_tower_target": "TWR_DEL_902", "evidence_id": "EVPBU00105"},
        {"communication_id": "CDR_BST_06", "source_phone_id": "PH04296", "target_phone_id": "PH02372", "timestamp": "2026-06-07 09:41:33", "duration_seconds": 420, "cell_tower_source": "TWR_DEL_401", "cell_tower_target": "TWR_DEL_812", "evidence_id": "EVPBU00121"}
    ]
}

SAMPLE_SCATTER_GATHER = {
    "source_type": "TRANSACTION_STREAM",
    "feed_id": "STREAM-SCATTER-2026-0820",
    "financial_institution": "Private Commercial Banking Core",
    "time_window": "2026-08-20 11:00:00 to 2026-08-20 13:40:00",
    "records": [
        {"transaction_id": "TX_SCT_01", "source_account_id": "A00055", "target_account_id": "A00056", "amount": 15000.0, "currency": "INR", "timestamp": "2026-08-20 11:05:00", "channel": "IMPS", "evidence_id": "EVD_SCT_01"},
        {"transaction_id": "TX_SCT_02", "source_account_id": "A00055", "target_account_id": "A00057", "amount": 15000.0, "currency": "INR", "timestamp": "2026-08-20 11:15:00", "channel": "IMPS", "evidence_id": "EVD_SCT_02"},
        {"transaction_id": "TX_SCT_03", "source_account_id": "A00055", "target_account_id": "A00058", "amount": 15000.0, "currency": "INR", "timestamp": "2026-08-20 11:25:00", "channel": "IMPS", "evidence_id": "EVD_SCT_03"},
        {"transaction_id": "TX_SCT_04", "source_account_id": "A00055", "target_account_id": "A00059", "amount": 15000.0, "currency": "INR", "timestamp": "2026-08-20 11:35:00", "channel": "IMPS", "evidence_id": "EVD_SCT_04"},
        {"transaction_id": "TX_SCT_05", "source_account_id": "A00056", "target_account_id": "A00064", "amount": 14850.0, "currency": "INR", "timestamp": "2026-08-20 13:10:00", "channel": "RTGS", "evidence_id": "EVD_SCT_05"},
        {"transaction_id": "TX_SCT_06", "source_account_id": "A00057", "target_account_id": "A00064", "amount": 14800.0, "currency": "INR", "timestamp": "2026-08-20 13:20:00", "channel": "RTGS", "evidence_id": "EVD_SCT_06"},
        {"transaction_id": "TX_SCT_07", "source_account_id": "A00058", "target_account_id": "A00064", "amount": 14900.0, "currency": "INR", "timestamp": "2026-08-20 13:30:00", "channel": "RTGS", "evidence_id": "EVD_SCT_07"}
    ]
}

SAMPLES = {
    "fir": SAMPLE_FIR_MULE,
    "structuring": SAMPLE_TRANSACTIONS_STRUCTURING,
    "cdr": SAMPLE_CDR_BURST,
    "scatter": SAMPLE_SCATTER_GATHER
}
