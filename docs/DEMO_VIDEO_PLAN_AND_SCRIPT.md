# ORION: Video Demonstration Blueprint & Script
## Smart India Hackathon 2026 — Problem Statement ID: 26184
### **ORION: Graph-Aware Prediction of Cyber-Fraud Cash-Out Hotspots and Fund-Freezing Recommendations**
#### **Nodal Agency:** Ministry of Home Affairs (MHA) | Indian Cybercrime Coordination Centre (I4C)

---

## 1. Video Production Master Plan

### 1.1 Objective & Target Audience
- **Target Audience:** SIH Jury, Ministry of Home Affairs evaluators, I4C cybercrime domain experts, and senior police leadership.
- **Core Message:** Financial cybercrime intervention fails when it is purely reactive. **ORION** bridges the velocity gap by predicting physical ATM cash-out hotspots and identifying mathematically optimal account chokepoints before stolen funds are liquidated.
- **Target Runtime:** **5 Minutes** (300 Seconds) — tightly paced, highly visual, zero fluff.

---

### 1.2 Technical & Recording Setup

| Parameter | Recommended Specification |
|---|---|
| **Resolution** | 1920 × 1080 (Full HD, 16:9), 60 FPS |
| **Theme** | Dark Control-Room Theme (Default in ORION) |
| **Audio** | Clear studio voiceover (Lavalier/Condenser mic), no background music or low ambient hum (-28 dB) |
| **Browser Setup** | Chrome / Chromium in Full Screen (`F11`), Zoom 100%, Bookmarks Bar hidden |
| **Local URLs** | Web Dashboard: `http://127.0.0.1:5173`<br>API Swagger: `http://127.0.0.1:8000/docs` |
| **Software** | OBS Studio / ScreenFlow / Camtasia (Use mouse click highlighting & subtle zoom-ins) |

---

### 1.3 Scene Breakdown & Time Budget

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ TOTAL RUNTIME: 5:00 (300 SECONDS)                                                      │
├──────────┬──────────────────────────────────────────┬──────────┬───────────────────────┤
│ Scene 01 │ Executive Hook & The Velocity Crisis     │ 00:00 - 00:40 (40s) │ Problem Statement & Crisis│
│ Scene 02 │ Command Center & NCRP Ingestion Feed     │ 00:40 - 01:15 (35s) │ Deliverable (c) Intro │
│ Scene 03 │ Graph Tracing & Laundering Typologies    │ 01:15 - 02:05 (50s) │ Deliverable (a) Graph │
│ Scene 04 │ Predictive Hotspot Forecasting & Heatmap │ 02:05 - 02:55 (50s) │ Deliverables (a) & (b)│
│ Scene 05 │ Multi-Channel Real-Time Alerting Hub     │ 02:55 - 03:35 (40s) │ Deliverable (d)       │
│ Scene 06 │ Node-Capacity Min-Cut Fund Freezing      │ 03:35 - 04:15 (40s) │ Actionable Freezing   │
│ Scene 07 │ Adversary Lab: Evasion & Model Hardening │ 04:15 - 04:45 (30s) │ Game-Theoretic Defense│
│ Scene 08 │ BSA Legal Compliance & Closing Mandate   │ 04:45 - 05:00 (15s) │ Institutional Wrap-Up │
└──────────┴──────────────────────────────────────────┴──────────┴───────────────────────┘
```

---

## 2. Complete Storyboard & Word-for-Word Script

---

### **SCENE 01: The Problem & The Velocity Gap (0:00 – 0:40)**
* **Screen:** Slide 1 / High-impact infographic with live camera PIP (Picture-in-Picture) or full-screen animated graphics showing the Indian cybercrime landscape, NCRP numbers, and the velocity breakdown.

#### Visual Directions:
1. **[0:00 - 0:15]** Show an infographic: *"National Cybercrime Reporting Portal (NCRP) receives 8,000+ complaints daily. Stolen funds hop through multi-tier mule accounts in minutes."*
2. **[0:15 - 0:30]** Show an animated timeline comparing syndicate cash-out velocity ($\le 3$ hours) vs. institutional reporting and freezing latency ($4\text{--}8$ hours). Highlight the red alert: *"CASH-OUT AT ATM: TRAIL GOES DARK"*.
3. **[0:30 - 0:40]** Fade in the ORION title card:
   **ORION: Graph-Aware Prediction of Cyber-Fraud Cash-Out Hotspots and Fund-Freezing Recommendations**
   *(Problem Statement ID: 26184 | Ministry of Home Affairs / I4C)*.

#### Voiceover Script:
> *"Every single day, the National Cybercrime Reporting Portal receives over 8,000 complaints. Across India, organized syndicates deploy automated networks of mule bank accounts to layer, structure, and disperse stolen money within minutes.*
>
> *Under the current reactive framework, by the time a victim reports fraud and banks attempt to intervene, the funds have already been liquidated in cash at local ATMs. Once converted to cash, digital audit trails vanish and fund recovery rates plummet.*
>
> *To solve Problem Statement 26184 for the Ministry of Home Affairs and I4C, we built **ORION**—a predictive analytics framework that forecasts likely cash withdrawal locations in advance, while pinpointing the exact account chokepoints to freeze before the cash is gone."*

---

### **SCENE 02: Command Center & Real-Time Ingestion (0:40 – 1:15)**
* **Screen:** ORION Command Center (`http://127.0.0.1:5173/command-center`).

#### Visual Directions:
1. **[0:40 - 0:50]** Screen displays the dark control-room Command Center. Mouse cursor sweeps across the top KPI strip:
   - *Active Complaints: 84*
   - *Traced Volume: ₹46.03 Lakh*
   - *High-Risk Identified Mules: 18*
   - *Dispatched Alerts: Live Counter*.
2. **[0:50 - 1:02]** Point to the **NCRP Live Complaint Stream**. Highlight a newly arrived high-value vishing case (e.g., `C00084` — ₹50,000 loss).
3. **[1:02 - 1:15]** Hover over the **Jurisdictional Mini-Map**, showing incident geographic density across districts without any third-party map tiles. Click on the button **"Inspect Case Trace"** on complaint `C00084`.

#### Voiceover Script:
> *"Welcome to the ORION Command Center—the operational nexus designed for I4C central monitors and State Cyber Police Control Rooms.*
>
> *The KPI strip provides immediate situational awareness across multi-district jurisdictions, tracking real-time complaint volumes, traced fraud capital, and identified mule accounts. On the left, the live NCRP complaint feed streams incoming citizen reports.*
>
> *Here, we observe complaint C00084—a victim reporting an unverified ₹50,000 debit. With a single click, ORION's graph reconstruction engine pulls the inter-bank transaction ledger and chronologically maps the fund trail."*

---

### **SCENE 03: Graph Tracing & Laundering Typology Detection (1:15 – 2:05)**
* **Screen:** ORION Case View (`http://127.0.0.1:5173/case?id=C00084`).

#### Visual Directions:
1. **[1:15 - 1:30]** The screen transitions smoothly to the Cytoscape directed multigraph.
   - Click the **"Play Trace"** animation button.
   - Watch money flow left-to-right from Victim (amber halo) $\to$ 3 Layer-1 Mules $\to$ 1 Central Collector Hub $\to$ 2 Layer-2 Cash-Out Mules.
2. **[1:30 - 1:45]** Click on the **Collector Node**. The right-hand inspection drawer slides in:
   - Highlight inferred role: `Mule Fan-In Identified` & `Layering Chain`.
   - Point to the repetition count and 24-hour receipt-coverage guard proving it is not a legitimate merchant.
3. **[1:45 - 1:55]** Click on an edge between accounts showing structured amounts just below ₹10,000 (Structuring / Smurfing).
4. **[1:55 - 2:05]** Point to the **Structural Anomaly Score** (OddBall star-shape power-law z-score) and **Temporal Burst Score** measuring acute activity concentration in a 48-hour sliding window.

#### Voiceover Script:
> *"In the Case Investigation Workbench, ORION models transactions as a chronological directed multigraph. By playing the trace, investigators visually witness fund dispersion in real time.*
>
> *Notice: the victim's money is immediately split into three Layer-1 mule accounts, forwarded within 45 minutes to a single collector account, and pooled before secondary dispersion.*
>
> *ORION's detection engine automatically evaluates five syndicate typologies. When we inspect the central hub, the system labels it with 'Mule Fan-In' and 'Layering Chain' evidence. Unlike naive heuristic rules, ORION incorporates a 24-hour receipt-coverage settlement guard, preventing false positives on commercial merchants.*
>
> *Simultaneously, our OddBall structural scorer identifies this account as a star-topology anomaly, while the temporal burst engine flags abnormal regularity in transaction velocity."*

---

### **SCENE 04: Predictive Analytics Engine & Risk Heatmap (2:05 – 2:55)**
* **Screen:** ORION Risk Heatmap Dashboard (`http://127.0.0.1:5173/heatmap`).

#### Visual Directions:
1. **[2:05 - 2:20]** Transition to the **Risk Heatmap**.
   - Show the full vector basemap rendering administrative district polygons (Indore Central, Malwa Vihar, Kshipra Nagar, Narmada Puram).
   - Emphasize the **"Simulated data"** and **"Offline Vector Mode"** badges (zero map tile requests).
2. **[2:20 - 2:32]** Point to the ATM markers:
   - Highlight the **bright pulsing dashed rings** indicating prospective ML predictions vs. solid historical dots.
   - Toggle the **Forecast Horizon** selector between **2 Hours**, **6 Hours**, and **24 Hours**, showing how the hotspot probability field shifts dynamically.
3. **[2:32 - 2:45]** Click on the top-ranked hotspot ATM (`ATM014` — Probability: 64.2%).
   - The inspector card opens on the right.
   - Zoom in on the **Top 3 Explainability Reasons** derived from tree SHAP feature attributions:
     1. *"Accounts in this chain withdrew here 4 times in the past 30 days"*
     2. *"Current fund location is 1 hop from withdrawal"*
     3. *"High spatial density cluster around collector hub"*.
4. **[2:45 - 2:55]** Click **"View Holdout Evaluation"** to briefly show the model benchmark drawer:
   - Highlight the **41.2% Top-5 Hit Rate** at the 6-hour window ($n=17$) and the 95% bootstrap confidence intervals.

#### Voiceover Script:
> *"Now we arrive at Key Deliverable B: the Risk Heatmap Dashboard.*
>
> *Crucially, this GIS engine operates entirely offline without external map tile servers or internet connectivity, making it deployable inside air-gapped police networks.*
>
> *The map visualizes our predictive analytics engine's forecasts. ATMs marked with pulsing dashed circles represent future withdrawal hotspots predicted by our Graph-Aware XGBoost model.*
>
> *Investigators can toggle between 2-hour, 6-hour, and 24-hour operational horizons. Clicking on the highest-risk ATM reveals not just a bare probability score, but full, plain-language explainability.*
>
> *Using tree SHAP feature attribution, ORION justifies the prediction: accounts in this chain have a 30-day spatial affinity to this location, and the money is currently just one graph hop away from liquidation. On held-out benchmark tests, our model achieves a 41.2% top-5 hit rate at the 6-hour horizon—outperforming recency baselines by nearly 30 percentage points."*

---

### **SCENE 05: Multi-Channel Alert & Notification System (2:55 – 3:35)**
* **Screen:** ORION Alerts Hub (`http://127.0.0.1:5173/alerts`).

#### Visual Directions:
1. **[2:55 - 3:10]** Click the **Notification Bell** on the TopBar (showing unread badge) $\to$ opens `/alerts`.
2. **[3:10 - 3:22]** Point to the newly dispatched **Critical Alert** for case `C00084`:
   - Highlight the severity pill: `CRITICAL` (Probability $\ge 50\%$).
   - Show the target: State Bank of India ATM014, Indore Central.
3. **[3:22 - 3:35]** Expand the **Multi-Channel Dispatch Log**:
   - Point to the **SMS Gateway Mock** dispatched to PCR Patrol Unit 12.
   - Point to the **Email Briefing** dispatched to District Cyber Police Station (DCCPS).
   - Point to the **REST Webhook** sent to State Police CAD and Bank CFCFRMS.
   - Click the button **"Acknowledge Alert"**; status updates immediately to `ACKNOWLEDGED`.

#### Voiceover Script:
> *"Forecasting is only valuable if it drives action. Key Deliverable D is ORION's automated Alert & Notification System.*
>
> *The moment an ATM's cash-out probability crosses our operational threshold, ORION triggers multi-channel dispatches.*
>
> *Here, a Critical Alert is logged for SBI ATM014. Within seconds, automated dispatches are routed across three channels:*
> *First, an urgent SMS alert to the nearest Police Control Room patrol vehicle to establish physical deterrence.*
> *Second, an encrypted intelligence dossier to the District Cyber Police Station.*
> *And third, an automated API webhook push to the bank's fraud monitoring desk.*
>
> *Field control officers acknowledge the dispatch with one click, preserving a full audit trail of inter-agency intervention."*

---

### **SCENE 06: Node-Capacity Min-Cut Fund Freezing (3:35 – 4:15)**
* **Screen:** ORION Fund Blocking Workbench (`http://127.0.0.1:5173/blocking?id=C00084`).

#### Visual Directions:
1. **[3:35 - 3:50]** Switch to the **Fund Blocking** screen for case `C00084`.
   - Point to the **Recommended Accounts to Freeze** table.
   - Notice that instead of freezing all 6 intermediate accounts or dead Layer-1 accounts, the algorithm identifies the **single collector hub** or the **2 terminal L2 mules**.
2. **[3:50 - 4:05]** Explain the mathematical formulation:
   - Callout box overlay: Directed Node Splitting: $v_{\text{in}} \to v_{\text{out}}$ with capacity $c(v) = 1.0 - 0.01 \times (\text{flow} / \text{total})$.
   - Show that already-cleared accounts are automatically assigned infinite capacity ($c = \infty$).
3. **[4:05 - 4:15]** Click **"Simulate Freeze"**:
   - Watch the animated **Before vs. After** progress bar:
     - *Reachable Funds Before:* ₹50,000 (100%)
     - *Reachable Funds After:* ₹0 (0%)
     - *Prevented Loss:* ₹50,000 (100% Stopped).

#### Voiceover Script:
> *"While police deploy to the ATM, what should the banks do? Freezing every account is unfeasible and causes collateral disruption to innocent citizens. Freezing the initial Layer-1 accounts is useless because the money has already moved.*
>
> *ORION solves this using a novel **Node-Capacity Minimum-Cut algorithm**.*
>
> *By applying directed node splitting with unit capacities and volume tiebreaking, ORION mathematically guarantees the **fewest possible accounts** are frozen to stop the **maximum volume of funds**.*
>
> *When we click 'Simulate Freeze', the max-flow algorithm demonstrates that blocking just these two identified bottleneck accounts halts 100% of the reachable stolen funds before withdrawal."*

---

### **SCENE 07: Adversary Lab — Evasion & Model Hardening (4:15 – 4:45)**
* **Screen:** ORION Adversary Lab (`http://127.0.0.1:5173/adversary`).

#### Visual Directions:
1. **[4:15 - 4:28]** Navigate to `/adversary`.
   - Focus on the **Evasion Cost Curve** chart.
   - Trace the **Cyan Line (Baseline Model)** dropping as criminal budget increases from ₹0 to ₹25,000.
   - Point out that detection is strictly non-increasing by construction.
2. **[4:28 - 4:38]** Highlight the **Purple Dashed Line (Hardened Model)**:
   - Show that the hardened curve stays substantially higher across all budget intervals.
3. **[4:38 - 4:45]** Scroll to the **Interactive Case Simulator**:
   - Select case `C00084` $\to$ Click **"Run Evasion Search"**.
   - Show the move log: *Move 1: Switch ATM (₹545)* $\to$ *Move 2: Delay 12h (₹10,764)*. Point to total evasion cost exceeding ₹11,000.

#### Voiceover Script:
> *"In Phase 5, we ask: what happens when criminals adapt? The **Adversary Lab** simulates a game-theoretic contest.*
>
> *Here, a criminal syndicate spends financial budget to evade our top-5 predictions by switching ATMs, delaying withdrawals, adding mule layers, or splitting amounts.*
>
> *The baseline curve in blue shows that evading ORION costs significant capital. More importantly, by retraining our models on adversary patterns from earlier cases, our **Hardened Model**—shown in purple—elevates detection rates across the entire budget frontier.*
>
> *The criminal must spend over 20% of their stolen proceeds just to lower detection risk, destroying syndicate profitability."*

---

### **SCENE 08: Statutory Compliance & Conclusion (4:45 – 5:00)**
* **Screen:** Return to Command Center / Case View with Section 63 BSA certificate preview overlay, then transition to closing title slide.

#### Visual Directions:
1. **[4:45 - 4:53]** Briefly show the **Section 63 BSA Evidentiary Certificate** modal with cryptographic SHA-256 hash chaining, software version tags, and timestamp logs.
2. **[4:53 - 5:00]** Cut to concluding title card:
   - **ORION: Graph-Aware Prediction of Cyber-Fraud Cash-Out Hotspots and Fund-Freezing Recommendations**
   - *Smart India Hackathon 2026 | Ministry of Home Affairs & I4C*
   - Team contact & repository links.

#### Voiceover Script:
> *"Every output in ORION adheres to Section 63 of the Bharatiya Sakshya Adhiniyam, 2023, generating cryptographically verified electronic evidence ready for court prosecution.*
>
> *ORION turns cybercrime intervention from a losing race against the clock into a proactive, data-driven shield for India's digital financial ecosystem. Thank you."*

---

## 3. Step-by-Step Rehearsal & Recording Checklist

Before starting OBS or screen recording, perform this 60-second preparation:

1. **Start Backend & Frontend:**
   ```bash
   ./run.sh
   ```
   *(Or in separate terminals: `python3 -m uvicorn app.main:app --port 8000` in backend, and `npm run dev` in frontend).*

2. **Verify Browser Display:**
   - Open Chrome at `http://127.0.0.1:5173`.
   - Verify green status: `"Backend online"`.
   - Hit `F11` (or `Cmd+Shift+F` on Mac) for borderless clean presentation.

3. **Pre-load Key Views in Tabs (Optional for quick switching):**
   - Tab 1: `http://127.0.0.1:5173/command-center`
   - Tab 2: `http://127.0.0.1:5173/case?id=C00084`
   - Tab 3: `http://127.0.0.1:5173/heatmap`
   - Tab 4: `http://127.0.0.1:5173/alerts`
   - Tab 5: `http://127.0.0.1:5173/blocking?id=C00084`
   - Tab 6: `http://127.0.0.1:5173/adversary`

4. **Speech Pacing:**
   - Total words: ~650 words.
   - Average speaking rate: 130 words per minute $\approx$ precisely 5 minutes.
   - Maintain a confident, steady, and professional tone throughout.
