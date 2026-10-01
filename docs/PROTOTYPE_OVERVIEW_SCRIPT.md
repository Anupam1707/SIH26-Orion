# ORION: Prototype Overview Script & Demonstration Guide
## Problem Statement ID: 26184 — Ministry of Home Affairs (MHA) / I4C
### **ORION: Graph-Aware Prediction of Cyber-Fraud Cash-Out Hotspots and Fund-Freezing Recommendations**

---

## Overview & Speaking Guidelines
* **Target Video Duration:** **2.5 to 3 Minutes** (~420–480 words at a steady, confident speaking cadence).
* **Tone:** Professional, authoritative, and operationally grounded for Law Enforcement Agencies (LEAs), Cyber Cells, and SIH evaluators.
* **Display Setup:** Open browser at `http://localhost:5173` in Full Screen (`F11` or `Cmd+Shift+F`), with the backend running on port `8000`.

---

## Demonstration Storyboard & Timing

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│ TOTAL RUNTIME: ~2 MIN 45 SEC (165 Seconds)                                              │
├─────────┬──────────────────────────┬──────────────┬─────────────────────────────────────┤
│ 00:00   │ Mandate & Problem Core   │ ~25 seconds  │ NCRP Scale, 8k complaints/day       │
│ 00:25   │ Command Center           │ ~25 seconds  │ Real-time Telemetry & Ingestion     │
│ 00:50   │ Case View Graph Engine   │ ~30 seconds  │ Multi-Hop Flow, Typologies & Hubs   │
│ 01:20   │ Predictive Risk Heatmap  │ ~30 seconds  │ 2h/6h Forecasts & SHAP Reasons      │
│ 01:50   │ Tactical Alerts Dispatch │ ~20 seconds  │ PCR Patrol SMS & CAD Integration    │
│ 02:10   │ Min-Cut Fund Freezing    │ ~25 seconds  │ Mathematical Chokepoint Blocking    │
│ 02:35   │ Compliance & Conclusion  │ ~10 seconds  │ Sec 63 BSA Digital Evidence & Impact│
└─────────┴──────────────────────────┴──────────────┴─────────────────────────────────────┘
```

---

## Detailed Voiceover Script with On-Screen Actions

### 1. Mandate & Problem Statement (0:00 – 0:25)
* **On Screen:** Start on the ORION dashboard (`http://localhost:5173`).
* **Visual Anchor:** Cursor rests over the brand logo: **`ORION`** and **`PS 26184 · MHA / I4C`**.

> **Expanded Voiceover:**  
> *"Across India, the National Cybercrime Reporting Portal receives more than 8,000 cyber fraud complaints every single day. Under the current workflow, response is largely reactive—by the time an investigation initiates, criminal syndicates have already layered the stolen funds across multiple tiers of mule accounts and cashed out at local ATMs.  
> 
> To solve Problem Statement 26184 for the Ministry of Home Affairs and I4C, we engineered **ORION**—an operational framework that shifts cybercrime response from reactive chasing to **proactive intervention**, predicting cash-out locations hours in advance and identifying optimal account chokepoints to freeze."*

---

### 2. Command Center — Live Telemetry & Ingestion (0:25 – 0:50)
* **On Screen:** `/command-center`
* **Mouse Action:** Glide across the top KPI strip (*Active Complaints, Traced Volume, High-Risk Accounts*), then click into complaint **`C00084`** (₹50,000 vishing complaint, Indore Central).

> **Expanded Voiceover:**  
> *"Our Command Center provides cyber cell officers with continuous, district-level situational awareness. Incoming complaints are ingested in sub-second timeframes, tracking cumulative volume at risk and flagging active mule accounts.  
> 
> When an urgent citizen complaint arrives—such as this fifty-thousand-rupee vishing case in Indore—investigators can drill down directly into the full multi-tier transaction graph."*

---

### 3. Case View — Graph Analytics & Typology Detection (0:50 – 1:20)
* **On Screen:** `/case?id=C00084`
* **Mouse Action:** Click **"Play Trace"**. Watch the animated money flow move left-to-right from Victim $\to$ L1 Mules $\to$ Collector Hub $\to$ L2 Mules. Click on the central Collector account node to open the Right Evidence Drawer.

> **Expanded Voiceover:**  
> *"In Case View, ORION reconstructs the money trail across banking institutions. Pressing 'Play Trace' animates how the fraudster immediately splits victim capital across multiple Layer-1 accounts before aggregating into a central collector hub.  
> 
> In the background, our rules engine scans for five complex laundering typologies—tagging this account with 'Mule Fan-In' and 'Layering Chain'. Crucially, ORION incorporates settlement window guards to ensure innocent high-volume e-commerce merchants are not falsely classified as criminal mules."*

---

### 4. Predictive Risk Heatmap — Forecasting Withdrawal Hotspots (1:20 – 1:50)
* **On Screen:** `/heatmap`
* **Mouse Action:** Show the offline district canvas map. Toggle between the **2h** and **6h** time horizon filters. Click on the highest-risk red ATM marker (**ATM014**).

> **Expanded Voiceover:**  
> *"This is ORION's core innovation—the Predictive Risk Heatmap. Built entirely on an offline vector GIS engine, it operates without external map tile servers, preventing sensitive law enforcement data from leaking.  
> 
> By fusing Equirectangular Spatial Kernel Density with a Graph-Aware XGBoost model, ORION forecasts where the stolen cash will be withdrawn within a two-to-six-hour lead time. Selecting the top hotspot exposes transparent SHAP explainability: the model highlights that this specific ATM is one hop away from the collector, shares an active geographical cluster, and exhibits heightened withdrawal velocity."*

---

### 5. Alerts & Field Dispatch — Tactical Deterrence (1:50 – 2:10)
* **On Screen:** Click the TopBar notification bell $\to$ navigates to `/alerts`.
* **Mouse Action:** Highlight the `CRITICAL` alert generated for ATM014. Show the multi-channel dispatch payload (SMS, Email, Police CAD / 112 webhook). Click **"Acknowledge Alert"**.

> **Expanded Voiceover:**  
> *"Actionable intelligence is meaningless without swift dispatch. As soon as a cash-out probability crosses the operational threshold, ORION's multi-channel alert engine automatically triggers.  
> 
> It pushes geofenced SMS alerts and CAD dispatch webhooks directly to the nearest Police Control Room patrol van and local beat officers, positioning physical deterrence at the ATM before the courier arrives to withdraw."*

---

### 6. Fund Blocking Engine — Mathematical Min-Cut Freezing (2:10 – 2:35)
* **On Screen:** Navigate to `/blocking?id=C00084`.
* **Mouse Action:** Point out the 2 recommended bottleneck accounts. Click **"Simulate Freeze"**, showing reachable fund flow drop to ₹0.

> **Expanded Voiceover:**  
> *"Simultaneously, ORION solves the mathematical Node-Capacity Minimum Cut problem on the transaction network. Instead of blindly freezing dozens of downstream accounts—which causes severe operational friction—ORION pinpoints the exact two bottleneck accounts that sever all flow to cash-out points.  
> 
> Simulating the freeze confirms that one-hundred percent of reachable victim funds are safeguarded with minimal bank actions."*

---

### 7. Evidentiary Integrity & Closing (2:35 – 2:45)
* **On Screen:** Return to the main overview or show the Section 63 BSA certificate export.

> **Expanded Voiceover:**  
> *"Every algorithmic trace, model score, and timestamp generated by ORION is cryptographically logged in full compliance with Section 63 of the Bharatiya Sakshya Adhiniyam, 2023, making it courtroom-ready digital evidence.  
> 
> With proactive geospatial prediction and mathematical fund blocking, ORION empowers Indian Law Enforcement to turn the tide against cyber fraud syndicates. Thank you."*

---

## Presenter Quick Reference Card

| Step | Screen | Key Click / Action | Key Voice Cue |
| :--- | :--- | :--- | :--- |
| **1. Intro** | Home / TopBar | Point to ORION logo | *"8,000 complaints daily... reactive to proactive."* |
| **2. Telemetry** | `/command-center` | Hover KPIs $\to$ Click `C00084` | *"Live situational awareness... sub-second ingestion."* |
| **3. Trace** | `/case` | Click 'Play Trace' $\to$ Click Collector | *"Reconstructs multi-hop flow... merchant guards."* |
| **4. Forecast** | `/heatmap` | Toggle 2h/6h $\to$ Click ATM014 | *"Offline vector GIS... XGBoost & SHAP explainability."* |
| **5. Dispatch** | `/alerts` | Show SMS/CAD payload $\to$ Acknowledge | *"Direct dispatch to PCR vans before criminals arrive."* |
| **6. Freeze** | `/blocking` | Click 'Simulate Freeze' | *"Node-capacity Min-Cut... 100% reachable funds locked."* |
| **7. Close** | TopBar / Export | Wrap up | *"Section 63 BSA compliant... proactive interception."* |
