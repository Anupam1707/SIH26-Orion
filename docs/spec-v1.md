# CLAUDE.md — MuleTrail Demo Build Spec

> **For Claude Code.** This file is the build brief for the MuleTrail demo (Smart India Hackathon PS 184).
> Build it **phase by phase** (Section 12). After each phase: run the phase's checks, summarise what changed, and **stop for review** before starting the next phase.

---

## 1. What we are building

MuleTrail is a demo web app that follows stolen money through a network of mule bank accounts and **predicts where it will be withdrawn as cash**, so banks can freeze it first.

It runs entirely on **simulated data**. One scripted fraud case plays from complaint to frozen funds in about 3 minutes:

1. A victim in Indore loses ₹50,000 to a vishing call → complaint appears
2. The money is traced hop by hop: victim → 3 layer-1 mules → collector → 2 layer-2 accounts
3. The laundering pattern is detected and labelled, with its signals
4. The map lights up the ATMs where cash-out is most likely, with probability, time window, and reasons
5. Alerts go to police and the bank (mocked, shown in-app)
6. The system recommends which accounts to freeze; a simulated freeze shows money stopped
7. Adversary mode: a simulated criminal changes tactics; the app shows what it cost them to evade

**Audience:** SIH judges. The demo must be honest (simulated data labelled as such), explainable (every score shows its reasons), and must never crash on stage.

---

## 2. Hard constraints

- **Offline-first.** Must run with no internet. No map tile servers, no CDN fonts, no external APIs at runtime.
- **Deterministic.** A fixed seed in the scenario file; the scripted case plays identically every run.
- **One command to start.** `./run.sh` (or `make demo`) starts backend + frontend.
- **Every screen interactive within 2 seconds.** Precompute model outputs at startup.
- **No hardcoded demo numbers in the UI.** Every number shown must come from the scenario, the graph, or a model output.
- **No real personal or financial data.** All names, account numbers, phone numbers, coordinates are fictional.
- **Label simulated/mocked things on screen.** A persistent "Simulated data" badge; mocked alert channels labelled "Mock delivery".
- **Explainability everywhere.** No bare scores — every prediction, alert, and recommendation carries its reasons and links to source records.

---

## 3. Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Language (backend) | Python 3.11 | |
| API | FastAPI + Uvicorn + Pydantic v2 | |
| Simulation | Mesa 3.x | Mesa 3 changed its API (no schedulers; `model.agents`). If it causes friction, a plain-Python step loop with the same agent classes is acceptable — keep the agent interface. |
| Graph | NetworkX (in-memory) | Neo4j is **optional**; the demo must work without it. |
| Models | scikit-learn (KDE), XGBoost | |
| Data | pandas, numpy | |
| Tests | pytest | |
| Frontend | React 18 + Vite + TypeScript | |
| Styling | Tailwind CSS | Dark theme |
| Map | Leaflet via react-leaflet, **no tile layer** | Render synthetic district polygons from a local GeoJSON as the basemap |
| Graph view | Cytoscape.js (react-cytoscapejs) | Left-to-right layout (`breadthfirst` or `dagre`) |
| Charts | Recharts | |

Pin versions in `requirements.txt` and `package.json`.

---

## 4. Repository structure

```
muletrail/
├── CLAUDE.md
├── run.sh                      # starts backend + frontend
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py             # FastAPI app, startup precompute
│   │   ├── state.py            # in-memory demo state + reset
│   │   ├── api/                # routers, one per screen area
│   │   ├── sim/                # scenario loader, agents, model, runner
│   │   ├── graph/              # graph builder, case tracing
│   │   ├── detect/             # typology rules, oddball, temporal
│   │   ├── predict/            # baseline, kde, xgb, features, evaluation
│   │   ├── block/              # min-cut fund blocking
│   │   ├── adversary/          # evasion moves, greedy search
│   │   └── alerts/             # alert generation, mock delivery store
│   ├── scenarios/
│   │   └── indore_demo.json    # the seeded demo scenario
│   └── tests/
└── frontend/
    ├── package.json
    ├── public/districts.geojson
    └── src/
        ├── api/                # typed API client
        ├── components/
        ├── screens/            # 6 screens
        └── lib/format.ts       # ₹ lakh/crore + IST formatting
```

---

## 5. Data model

All IDs are strings with a prefix. Timestamps are ISO 8601 in IST (`+05:30`).

| Entity | Key fields |
|---|---|
| `District` | `id` (D01…), `name`, `polygon` (GeoJSON), `centroid` |
| `ATM` | `id` (ATM001…), `district_id`, `lat`, `lng`, `bank` |
| `Account` | `id` (A00001…), `holder_id`, `bank`, `home_district_id`, `opened_at`, `role_truth` (hidden ground truth: `citizen`/`victim`/`mule_l1`/`mule_l2`/`mule_l3`/`collector`) |
| `Person` | `id` (P00001…), `name` (fictional), `district_id` |
| `Transaction` | `id` (T…), `src`, `dst`, `amount_inr`, `ts`, `channel` (UPI/IMPS/NEFT) |
| `Withdrawal` | `id` (W…), `account_id`, `atm_id`, `amount_inr`, `ts`, `network_id` (ground truth, hidden from models) |
| `Complaint` | `id` (C…), `victim_account_id`, `amount_inr`, `reported_at`, `district_id`, `description` |
| `FraudNetwork` | `id` (N_A…), `strategy`, `members` (ground truth) |

Ground truth fields (`role_truth`, `network_id`, `members`) are used **only for evaluation and the scenario**, never as model inputs.

Also export `ground_truth.csv`: every planted structure with type, member IDs, and time window.

---

## 6. Scenario file (`scenarios/indore_demo.json`)

Single source of truth for the world. Shape:

```json
{
  "seed": 42,
  "start_date": "2026-06-01",
  "days": 90,
  "districts": [ { "id": "D01", "name": "Indore Central", "polygon": [...] } ],
  "atms_per_district": 15,
  "citizens": 1800,
  "networks": [
    { "id": "N_A", "strategy": "rotate_near_collector", "mules": { "l1": 4, "l2": 2 }, "atm_pool_size": 3, "frauds_per_week": 3 },
    { "id": "N_B", "strategy": "hop_district",           "mules": { "l1": 5, "l2": 3 }, "frauds_per_week": 2 },
    { "id": "N_C", "strategy": "split_many_atms",        "mules": { "l1": 6, "l2": 2 }, "split_max_inr": 20000, "frauds_per_week": 2 }
  ],
  "demo_case": {
    "network_id": "N_A",
    "victim_district": "D01",
    "amount_inr": 50000,
    "inject_at": "2026-08-30T10:15:00+05:30",
    "path": { "l1_mules": 3, "collector": 1, "l2_accounts": 2 }
  }
}
```

- Use 4 fictional districts around Indore with plausible but **fictional** coordinates.
- About 60 ATMs total; about 2,000 accounts.
- Days 1–90 are history; the demo case is injected at the end.

---

## 7. Simulator (`backend/app/sim/`)

Agent-based model: each agent has a `step()` called once per simulated hour.

| Agent | Behaviour per step |
|---|---|
| `Citizen` | Occasional normal transfers (salary, rent, shopping); occasional small ATM withdrawals near home. **Essential background noise.** |
| `Caller` | Per its network's `frauds_per_week`, picks a random citizen as victim; the victim transfers a sampled amount (₹10k–₹2L, log-normal) to a layer-1 mule. |
| `Mule` (L1/L2/L3) | Forwards 92–98% of received funds within 5–45 minutes to the next layer; keeps the rest. |
| `Collector` | Receives from several L1 mules within a 48h window; forwards ~95% onward in one or two transfers. |
| `CashOutAgent` | Withdraws from final-layer accounts according to the network strategy (below), 2–10 hours after funds arrive. |

**Cash-out strategies (the pattern the prediction model must learn):**

- `rotate_near_collector` — rotates among a fixed pool of 3 ATMs near the collector's district
- `hop_district` — after each fraud, moves to a neighbouring district and uses ATMs there
- `split_many_atms` — splits cash into chunks up to `split_max_inr` across many ATMs in one district

**Outputs:** in-memory tables for all entities in Section 5, plus `ground_truth.csv`.

**Tests:** same seed → identical output; each network produces fan-in, layering, and withdrawals matching its strategy; the demo case exists with exactly the configured path.

---

## 8. Graph and detection

### 8.1 Graph (`graph/`)
- Directed `MultiDiGraph`: account nodes, transaction edges (`amount_inr`, `ts`).
- `trace_case(complaint_id)` → the money path from the victim account forward, following edges after the fraud timestamp, up to 5 hops, pruning branches whose cumulative traced amount falls below 5% of the original.
- Returns nodes with their **inferred role** (from detection, not ground truth), edges with amount and time, and hop order for animation.

### 8.2 Typology rules (`detect/rules.py`)
Implement as functions over the graph; each returns matches with evidence (the transactions that triggered it):

| Rule | Logic |
|---|---|
| Mule fan-in | Account receiving from ≥ 8 distinct senders within 48h, then forwarding ≥ 90% of inflow within 24h |
| Layering chain | Path of 5 accounts, each hop < 30 min after the previous, each amount 92–98% of the previous |
| Structuring | Account with ≥ 3 transfers between ₹9,000 and ₹9,900 |
| Scatter | Account sending to ≥ 6 distinct receivers within 2h |
| Rapid pass-through | Account forwarding ≥ 90% of each inflow within 60 minutes, ≥ 3 times |

**Lesson from the prototype:** single-condition rules produce many false positives. Always require the repetition/time-window conditions above.

### 8.3 OddBall structural score (`detect/oddball.py`)
Port this logic exactly:
1. For each account: `egonet_nodes` = distinct neighbours (both directions), `egonet_edges` = edges among those neighbours.
2. Keep accounts with `egonet_nodes > 1` and `egonet_edges > 0`.
3. Fit `log10(edges) = alpha * log10(nodes) + intercept` with `np.polyfit`.
4. `expected = 10 ** (alpha * log10(nodes) + intercept)`.
5. `score = max(e, exp) / min(e, exp) * log10(|e − exp| + 1)`.
6. `shape = 'STAR'` if `e < exp` else `'NEAR_CLIQUE'`.
7. **Normalise within each shape group** (z-score per shape). The raw score is biased toward cliques; without this, star-shaped mule hubs are under-ranked.

### 8.4 Temporal burst score (`detect/temporal.py`)
Port this logic exactly:
1. For each account with ≥ 5 outgoing transactions, find its **single densest 48-hour window** (sliding window over sorted timestamps).
2. Skip if that window holds < 5 transactions.
3. Inside the window only: `cv_gap` = std/mean of gaps between transactions (minutes); `cv_amount` = std/mean of amounts; `burst_ratio` = window count / total count.
4. `temporal_score = -z(cv_gap) + z(burst_ratio) - z(cv_amount)`.
5. **Guard `z()` against zero standard deviation** — return zeros for that component. (The prototype produced NaN when every account had `cv_gap = 0`.)

**Lesson from the prototype:** measuring regularity across an account's whole history dilutes a short burst. Always measure inside the densest window.

### 8.5 Combined account risk
`risk = rules_hit_count + max(oddball_z, 0) + max(temporal_score, 0)` (normalised to 0–1). Each account returns its contributing signals for the explanation panel.

---

## 9. Cash-out prediction (`predict/`)

**Prediction unit:** for a given fraud case, rank **ATMs** by probability that the case's money is withdrawn there within the next 2h / 6h / 24h. The heatmap renders these ATM probabilities as heat.

### 9.1 Three models (all must be selectable in the UI)

| Model | Logic |
|---|---|
| Baseline | Rank ATMs by how recently accounts in the traced chain (or their neighbours) last withdrew there. Probability from a simple recency decay. |
| KDE | `sklearn.neighbors.KernelDensity` over past withdrawal coordinates by accounts linked to the chain; score each ATM by density. Tune bandwidth on training days. |
| Graph-aware XGBoost | Binary classifier per (case, ATM) pair. Features below. |

**XGBoost features per (case, ATM):**
- distance from ATM to the chain's final-layer accounts' home districts
- count of past withdrawals at this ATM by chain-linked accounts (last 7 / 30 days)
- KDE density at the ATM
- hops from victim to the account currently holding the money
- temporal burst score of chain accounts
- hour of day and day of week of the prediction time
- whether the ATM's district differs from the last-used district (captures `hop_district`)

### 9.2 Evaluation (`predict/evaluate.py`)
- **Time-based split:** train on days 1–70, test on days 71–90. **Never a random split.**
- Build test cases from every fraud in days 71–90.
- Metrics per model: **Precision@5** (share of the top-5 ATMs where a withdrawal occurred in the window), **hit rate** (share of cases where the actual cash-out ATM is in the top 5), per time window.
- Always report the baseline beside the other models. Expose results via API for the UI.
- If the graph-aware model does not beat the baseline, say so in the output — do not tune the test set to make it win.

### 9.3 Explanations
Every ATM prediction returns its top 3 reasons in plain language, e.g. "This network withdrew here 4 times in 30 days", "Money is 1 hop from cash-out", "Network usually moves to a new district after each fraud". Use XGBoost feature contributions (`pred_contribs=True`) mapped to templated sentences.

---

## 10. Fund blocking (`block/`)

**Goal:** recommend the fewest accounts to freeze that stop the most money reaching cash-out.

**Method — node-capacity min-cut:**
1. Take the traced case subgraph.
2. Add a super-source `S` → victim account (infinite capacity) and every final-layer / withdrawing account → super-sink `T` (infinite capacity).
3. Freezing acts on **accounts (nodes)**, but min-cut cuts **edges**. Convert with **node splitting**: replace each account `v` with `v_in → v_out`, capacity = total money that flowed through `v`; original edges run `u_out → v_in` with infinite capacity. The victim, `S`, and `T` are not split.
4. `networkx.minimum_cut(G, 'S', 'T')` → the cut's `v_in → v_out` edges are the accounts to freeze.
5. If the cut has more than `k` accounts (default `k = 3`), fall back to greedy: repeatedly freeze the account whose removal most reduces `networkx.maximum_flow_value`.

**Simulate freeze:** remove the chosen accounts, recompute max flow from victim to sink. Return money reachable **before** and **after**, and the share stopped.

**Tests:** on a hand-built graph with an obvious single chokepoint, the recommender returns that chokepoint.

---

## 11. Adversary (`adversary/`)

A simulated criminal changes cash-out behaviour to avoid the predicted top-5 ATMs.

**Moves and costs:**

| Move | Effect | Cost |
|---|---|---|
| Switch ATM | Withdraw at an ATM outside the top-5 | ₹500 + travel (₹10/km) |
| Delay | Wait 12h before withdrawing | 12 hours (risk of freeze) |
| Add mule hop | Insert one extra layer | ₹3,000 (mule's cut) + 1 hour |
| Split amount | Split across 2 more ATMs | ₹1,000 per extra ATM |

**Greedy search:** from the demo case, repeatedly apply the move with the largest drop in "detected" probability (actual cash-out ATM in the model's top-5) per unit cost, until undetected or budget exhausted.

**Evasion cost curve:** for budgets ₹0–₹25,000 in steps, run the search over the test cases and record the detection rate. Plot detection rate vs. budget.

**Hardening:** retrain XGBoost with training data augmented by adversary-generated cash-outs; recompute the curve. The UI shows both curves.

Every move is logged for the Adversary Lab screen.

---

## 12. Build phases

Build in order. Each phase ends with its checks passing and a short summary. **Stop after each phase.**

### Phase 0 — Scaffold
- Repo structure, `run.sh`, FastAPI `/health`, React app shell with sidebar (6 screen stubs), top bar with persona switcher and notification bell, "Simulated data" badge, dark theme, `lib/format.ts` (₹ in lakh/crore style, IST).
- **Check:** `./run.sh` starts both; all 6 screens reachable.

### Phase 1 — Scenario + simulator
- Scenario loader, agents, model, runner, ground truth export, `districts.geojson`.
- **Check:** pytest — determinism, per-network patterns, demo case path.

### Phase 2 — Graph + detection + Case View + Command Center
- Graph builder, `trace_case`, rules, OddBall, temporal, combined risk.
- Command Center: KPI strip, complaint feed, mini map.
- Case View: Cytoscape graph left to right, role colours, "Play" animation, side panel with pattern and signals, clickable nodes.
- **Check:** demo case traces with the configured path; its chain is labelled mule fan-in + layering.

### Phase 3 — Prediction + Risk Heatmap
- Three models, evaluation, explanations. Precompute at startup.
- Heatmap: district polygons, ATM points, heat by probability, time-window and threshold filters, model switcher, explanation card.
- **Check:** evaluation table printed with baseline beside others; heatmap renders offline.

### Phase 4 — Alerts + Fund Blocking
- Alert generation when an ATM crosses the threshold; mock delivery log (SMS/email/API) in-app; alert statuses.
- Fund Blocking screen: ranked recommendations, before/after bar, "Simulate freeze".
- **Check:** min-cut test passes; demo case shows money reachable dropping after freeze.

### Phase 5 — Adversary Lab
- Moves, greedy search, evasion cost curves (baseline vs hardened), move log, toggle.
- **Check:** the curve is monotone non-increasing in detection rate as budget rises.

### Phase 6 — Demo polish
- **Demo script mode:** a "Start demo" button that injects the complaint and walks the 7 steps with "Next" prompts.
- **Reset** button (< 5 s) restoring initial state.
- Offline verification (no network requests at runtime), projector-readable sizes (≥ 14 px body), 1080p layout.
- **Check:** full story completes three times in a row with resets between.

---

## 13. API endpoints

| Method | Path | Returns |
|---|---|---|
| GET | `/health` | status |
| GET | `/summary` | KPI strip values |
| GET | `/complaints` | complaint feed |
| POST | `/demo/start` | injects the scripted complaint |
| POST | `/demo/reset` | restores initial state |
| GET | `/cases/{complaint_id}/trace` | nodes, edges, hop order, detected patterns |
| GET | `/accounts/{id}` | account details, signals, source transactions |
| GET | `/districts` | GeoJSON |
| GET | `/atms` | ATM list |
| GET | `/predictions/{complaint_id}?model=&window=` | ranked ATMs with probability and reasons |
| GET | `/evaluation` | metrics per model per window |
| GET | `/alerts` / POST `/alerts/{id}/ack` | alert list / acknowledge |
| GET | `/block/{complaint_id}` | freeze recommendations |
| POST | `/block/{complaint_id}/simulate` | before/after money reachable |
| POST | `/adversary/run` | move log + detection result |
| GET | `/adversary/curves` | evasion cost curves |

---

## 14. UI rules

- Dark control-room theme; high contrast for projectors.
- Predicted items look different from observed ones: **dashed lines, lighter fill**.
- Every score has an adjacent "Why?" that opens its reasons and source records.
- ₹ amounts in Indian format (₹50,000 · ₹1.2 lakh · ₹3.4 crore); times in IST.
- Loading states never blank the screen; data is precomputed.
- Persona switcher (I4C / Investigator / Bank officer) changes the default screen and which actions are highlighted — no real auth.

---

## 15. Non-goals

- No real authentication, real SMS/email, or real bank/CFCFRMS integration
- No mobile app
- No Neo4j dependency at runtime (optional adapter only)
- No LLM chat interface
- No reinforcement learning for the adversary (greedy search only)

---

## 16. How to work

- Before writing code in each phase, list the files you will create or change.
- Write tests alongside logic, not after.
- Prefer small, readable functions; type hints in Python, strict TypeScript.
- If a requirement here is ambiguous or conflicts with another, **ask** rather than guess.
- Never hardcode a number in the UI to make the demo look better. If a model underperforms, surface it honestly.
