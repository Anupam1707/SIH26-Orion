# Module 05: Alert & Notification System
## Key Deliverable Component (d) — Technical Specification

---

## 1. Objectives & Dispatch Architecture

The **Alert & Notification System** transforms predictive analytics and min-cut blocking outputs into actionable field intelligence. When an ATM's cash-out probability crosses pre-configured risk thresholds, the system dispatches real-time multi-channel alerts across:
1. **Law Enforcement Dispatch:** Local Police Control Rooms (PCR) and District Cyber Crime Police Stations (DCCPS).
2. **Bank Fraud Monitoring Desks:** Immediate ATM security officer alerts and cash replenishment cash-hold advisories.
3. **I4C Central Coordination:** Inter-jurisdictional intelligence aggregation.

---

## 2. Alert Generation & Severity Engine

### 2.1 Trigger Criteria
Alerts are generated systematically when ATM cash-out probability predictions satisfy configurable operational rules:
- **Critical Alert ($\text{Probability} \ge 0.50$):** High-confidence immediate cash-out predicted within 2–6 hours. Requires immediate PCR patrol deployment and ATM cash-cassette lockdown advisories.
- **High Alert ($0.30 \le \text{Probability} < 0.50$):** Significant probability of withdrawal. Dispatches electronic notices to bank branch nodal officers and local beat officers.
- **Medium Alert ($0.15 \le \text{Probability} < 0.30$):** Elevated surveillance notice for monitoring desks.

### 2.2 Payload Structure
Each dispatched alert contains a structured JSON payload:
```json
{
  "id": "ALT-2026-0830-001",
  "complaint_id": "C00084",
  "severity": "critical",
  "atm_id": "ATM014",
  "bank": "State Bank of India",
  "district": "Indore Central",
  "coordinates": [22.7196, 75.8577],
  "probability": 0.642,
  "window_hours": 6,
  "reasons": [
    "Accounts in this chain withdrew here 4 times in the past 30 days",
    "Current fund location is 1 hop from withdrawal",
    "High spatial density cluster around collector hub"
  ],
  "dispatched_at": "2026-08-30T10:45:00+05:30",
  "status": "triggered",
  "channels": ["sms", "email", "api", "dashboard"]
}
```

---

## 3. Multi-Channel Mock Delivery Engine

To adhere to the offline, zero-external-dependency requirement while demonstrating end-to-end operational viability, the platform integrates a high-fidelity **Mock Delivery Store**:

### 3.1 Simulated Channels
1. **SMS Gateway:** Formatted for SMS delivery to field patrol officers:
   > `[MHA-I4C ALERT] URGENT: High-risk ATM cash-out predicted at SBI ATM014 (Indore Central) within 6h (Prob: 64%). Case C00084. Deploy patrol immediately.`
2. **Email Dispatch:** Rich HTML/Text intelligence briefing dispatched to DCCPS nodal officers and Bank Fraud Risk units containing case trace summaries and suspect account numbers.
3. **Automated API Webhook:** REST payload pushed to State Police CAD (Computer Aided Dispatch) and Bank CFCFRMS gateways.
4. **Dashboard In-App Notifications:** Real-time badge counter on TopBar with instant sound trigger and banner overlay.

### 3.2 Investigator Lifecycle & Acknowledgement
Field investigators and control room operators can manage the alert lifecycle directly within the `/alerts` screen:
- **Triggered:** Newly dispatched alert awaiting field verification.
- **Acknowledged:** Officer acknowledges receipt and confirms unit dispatch (`POST /alerts/{id}/ack`).
- **Resolved / Intervened:** Status updated upon successful fund interception or patrol inspection.
