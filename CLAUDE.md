# CLAUDE.md — MuleTrail Demo Build Spec

> **For Claude Code.** This file is the build brief for the MuleTrail demo (Smart India Hackathon PS 26184 | Ministry of Home Affairs / I4C).
> Build it **phase by phase** (Section 12). After each phase: run the phase's checks, summarise what changed, and **stop for review** before starting the next phase.
>
> Spec v2 (2026-09-29). v1 is kept at `docs/spec-v1.md`; Section 17 lists every change and why.

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
- **One command to start.** `./run.sh` (macOS/Linux/Git Bash) or `.\run.ps1` (Windows PowerShell) starts backend + frontend. The demo laptop runs Windows — `run.ps1` is the primary path.
- **Every screen interactive within 2 seconds.** Precompute model outputs once and cache them (Section 12, Phase 0 and Section 16).
- **No hardcoded demo numbers in the UI.** Every number shown must come from the scenario, the graph, or a model output.
- **No real personal or financial data.** All names, account numbers, phone numbers, coordinates are fictional.
- **Label simulated/mocked things on screen.** A persistent "Simulated data" badge; mocked alert channels labelled "Mock delivery".
- **Explainability everywhere.** No bare scores — every prediction, alert, and recommendation carries its reasons and links to source records.
- **No future leakage.** Nothing the system shows or computes may use records timestamped after the current demo clock (Section 7.3).

---

## 3. Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Language (backend) | Python 3.11 | |
| API | FastAPI + Uvicorn + Pydantic v2 | |
| Simulation | Mesa 3.x | Mesa 3 changed its API (no schedulers; `model.agents`). If it causes friction, a plain-Python step loop with the same agent classes is acceptable — keep the agent interface. Either way, sub-hour timing uses the event queue in Section 7.2. |
| Graph | NetworkX (in-memory) | Neo4j is **optional**; the demo must work without it. |
| Models | scikit-learn (KDE), XGBoost | |
| Data | pandas, numpy | |
| Tests | pytest | |
| Frontend | React 18 + Vite + TypeScript | |
| Styling | Tailwind CSS | Dark theme. System font stack only — no web fonts. |
| Map | Leaflet via react-leaflet, **no tile layer** | Render synthetic district polygons from `/districts` as the basemap. Draw ATMs with `CircleMarker` — Leaflet's default marker images break under Vite bundling. |
| Graph view | Cytoscape.js (react-cytoscapejs) | Left-to-right layout: `dagre` via the `cytoscape-dagre` extension (a separate package), or built-in `breadthfirst` |
| Charts | Recharts | |

Pin versions in `requirements.txt` and `package.json`.

---

## 4. Repository structure

```
muletrail/
├── CLAUDE.md
├── run.sh                      # starts backend + frontend (bash)
├── run.ps1                     # same, for Windows PowerShell (primary on the demo laptop)
├── docs/spec-v1.md             # original spec, for reference
├── backend/
│   ├── requirements.txt
│   ├── .cache/                 # precomputed world + models, keyed by scenario hash (gitignored)
│   ├── app/
│   │   ├── main.py             # FastAPI app, loads precompute cache at startup
│   │   ├── precompute.py       # `python -m app.precompute` builds the cache
│   │   ├── state.py            # in-memory demo state, demo clock, snapshot + reset
│   │   ├── api/                # routers, one per screen area
│   │   ├── sim/                # scenario loader, agents, event queue, model, runner
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
    └── src/
        ├── api/                # typed API client
        ├── components/
        ├── screens/            # 6 screens (Section 14)
        └── lib/format.ts       # ₹ lakh/crore + IST formatting
```

District polygons have one source: the scenario file. The frontend fetches them from `GET /districts`; there is no hand-maintained GeoJSON copy.

---

## 5. Data model

All IDs are strings with a prefix. Timestamps are ISO 8601 in IST (`+05:30`).

| Entity | Key fields |
|---|---|
| `District` | `id` (D01…), `name`, `polygon` (GeoJSON), `centroid`, `neighbours` (district ids) |
| `ATM` | `id` (ATM001…), `district_id`, `lat`, `lng`, `bank` |
| `Account` | `id` (A00001…), `holder_id`, `bank`, `home_district_id`, `opened_at`, `role_truth` (hidden ground truth: `citizen`/`merchant`/`victim`/`mule_l1`/`mule_l2`/`collector`) |
| `Person` | `id` (P00001…), `name` (fictional), `district_id` |
| `Transaction` | `id` (T…), `src`, `dst`, `amount_inr`, `ts`, `channel` (UPI/IMPS/NEFT), `fraud_id` (hidden ground truth, null for normal activity) |
| `Withdrawal` | `id` (W…), `account_id`, `atm_id`, `amount_inr`, `ts`, `network_id` + `fraud_id` (hidden ground truth) |
| `Complaint` | `id` (C…), `victim_account_id`, `amount_inr`, `incident_at` (victim-reported time of the fraud), `reported_at`, `district_id`, `description` |
| `FraudNetwork` | `id` (N_A…), `strategy`, `members` (ground truth) |

Ground truth fields (`role_truth`, `fraud_id`, `network_id`, `members`) are used **only for evaluation and the scenario**, never as model inputs, rule inputs, or explanation text.

Also export `ground_truth.csv`: every planted structure with type, member IDs, and time window.

---

## 6. Scenario file (`scenarios/indore_demo.json`)

Single source of truth for the world. Shape:

```json
{
  "seed": 42,
  "start_date": "2026-06-01",
  "days": 90,
  "districts": [ { "id": "D01", "name": "Indore Central", "polygon": [...], "neighbours": ["D02", "D03"] } ],
  "atms_per_district": 15,
  "citizens": 1800,
  "merchant_share": 0.02,
  "complaint_delay_min": [15, 90],
  "freeze_risk_per_hour": 0.02,
  "networks": [
    { "id": "N_A", "strategy": "rotate_near_collector", "transfer_style": "plain",      "collector_district": "D03", "mules": { "l1": 4, "l2": 2 }, "atm_pool_size": 3, "frauds_per_week": 3 },
    { "id": "N_B", "strategy": "hop_district",          "transfer_style": "structured", "collector_district": "D02", "mules": { "l1": 5, "l2": 3 }, "frauds_per_week": 2 },
    { "id": "N_C", "strategy": "split_many_atms",       "transfer_style": "scatter",    "collector_district": "D04", "mules": { "l1": 6, "l2": 6 }, "split_max_inr": 20000, "frauds_per_week": 2 }
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

- Use 4 fictional districts around Indore with plausible but **fictional** coordinates; `neighbours` drives `hop_district`.
- About 60 ATMs total; about 2,000 accounts.
- Days 1–90 (2026-06-01 00:00 to 2026-08-30 00:00 IST) are history. The demo case is injected at `inject_at`, and the simulator keeps running past it until the demo case has fully cashed out (Section 7.3).
- Every fraud (history and demo) produces a `Complaint`, reported `complaint_delay_min` minutes after the victim's last transfer.
- `collector_district` (per network) is where the collector and, for `rotate_near_collector` and `split_many_atms`, the layer-2 accounts and ATMs live. Every district needs at least one neighbour (`hop_district`).
- The loader validates all cross-references (neighbours, collector districts, the demo path against the network's mule counts, `inject_at` after history) and rejects a bad scenario before any work is done.

---

## 7. Simulator (`backend/app/sim/`)

### 7.1 Agents

Agent-based model: each agent has a `step()` called once per simulated hour.

| Agent | Behaviour |
|---|---|
| `Citizen` | Occasional normal transfers (salary, rent, shopping); occasional small ATM withdrawals near home. **Essential background noise.** |
| `Merchant` (a `Citizen` subtype, `merchant_share` of citizens) | Receives many small payments from distinct senders but does **not** forward most of it on quickly. These are the hard negatives for the fan-in rule. |
| `Caller` | Per its network's `frauds_per_week`, picks a random citizen as victim; the victim sends a sampled amount (₹10k–₹2L, log-normal) to **1–3 layer-1 mules** of that network, split into one transfer per mule. |
| `Mule` (L1) | Forwards 92–98% of each receipt to the network's collector within 5–45 minutes; keeps the rest. |
| `Collector` | Gathers all L1 forwards belonging to one fraud; 20–90 minutes after the last one arrives, forwards ~95% of the pooled amount to layer-2 accounts (see `transfer_style`). |
| `Mule` (L2) | Final layer. Holds the funds for cash-out. |
| `CashOutAgent` | Withdraws from L2 accounts according to the network strategy (below), 2–10 hours after funds arrive. |

**Topology (every network):** victim → L1 mules → collector → L2 accounts → ATM cash-out. There is no layer 3.

**Transfer styles (what the typology rules must be able to find):**

- `plain` — each hop is one transfer per receiving account (collector pays 1–2 L2 accounts).
- `structured` — L1 mules forward in chunks of ₹9,000–₹9,900 instead of one transfer.
- `scatter` — the collector pays all 6 L2 accounts within 2 hours.

**Cash-out strategies (the pattern the prediction model must learn):**

- `rotate_near_collector` — rotates among a fixed pool of 3 ATMs near the collector's district
- `hop_district` — after each fraud, moves to a neighbouring district and uses ATMs there
- `split_many_atms` — splits cash into chunks up to `split_max_inr` across many ATMs in one district

### 7.2 Event queue

Behaviour happens at minute resolution but `step()` is hourly, so agents do not act directly inside `step()` for timed actions. Instead they **schedule events** (`ts`, action) on a priority queue; each step executes, in timestamp order, every event with `ts` in `[t, t + 1h)`. Events may schedule further events, including within the same hour. Ties break on a deterministic sequence number.

### 7.3 Demo clock and leakage

- The precompute runs the simulation to completion, including the demo case's cash-out, so everything is ready at startup.
- `state.py` holds a **demo clock**. Every API response and every model input is filtered to records with `ts ≤ demo_clock`. Initially `demo_clock` = end of history; `/demo/start` and the demo script's "Next" steps advance it along the demo case.
- **Prediction time** for any case (demo or evaluation) = `max(complaint.reported_at, time the last transfer reached an L2 account)`. Predictions use only records up to prediction time. The case's own withdrawals are never visible to its prediction.

**Outputs:** in-memory tables for all entities in Section 5, plus `ground_truth.csv`.

**Tests:** same seed → identical output; each network produces the topology, transfer style, and withdrawals matching its configuration; the demo case exists with exactly the configured path; no withdrawal of a case precedes that case's prediction time by construction of the filter.

---

## 8. Graph and detection

### 8.1 Graph (`graph/`)
- Directed `MultiDiGraph`: account nodes, transaction edges (`amount_inr`, `ts`).
- `trace_case(complaint_id)` → the money path from the victim account forward, following edges after `complaint.incident_at`, up to 5 hops, pruning branches whose cumulative traced amount falls below 5% of the original.
- Returns nodes with their **inferred role** (from detection, not ground truth), edges with amount and time, and hop order for animation.

### 8.2 Typology rules (`detect/rules.py`)
Implement as functions over the graph; each returns matches with evidence (the transactions that triggered it). Thresholds are set to match this scenario's topology; they are scenario parameters, not magic numbers.

| Rule | Logic | Expected to fire on |
|---|---|---|
| Mule fan-in | Account receiving from ≥ 3 distinct senders within 6h, then forwarding ≥ 90% of that inflow within 24h — **and this has happened ≥ 2 times** in its history | Collectors |
| Layering chain | Path of ≥ 4 accounts (≥ 3 hops) where, for every intermediate account, money leaves < 3h after it arrived and the amount leaving is 85–98% of the amount that entered (summing same-window inflows and outflows, so pooling and splitting are handled) | victim → L1 → collector → L2 |
| Structuring | Account with ≥ 3 transfers between ₹9,000 and ₹9,900 | N_B L1 mules |
| Scatter | Account sending to ≥ 6 distinct receivers within 2h | N_C collector |
| Rapid pass-through | Account forwarding ≥ 90% of each inflow within 60 minutes, ≥ 3 times | L1 mules |

**Lesson from the prototype:** single-condition rules produce many false positives. Always require the repetition/time-window conditions above. Merchants must not trigger fan-in (they do not forward); a test asserts this.

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

**Expected coverage:** in this scenario the burst score fires mainly on N_B's structured L1 mules and N_C's scatter collector. N_A accounts usually have too few outgoing transfers and score 0 — that is expected, not a bug. Skipped accounts get `temporal_score = 0`.

### 8.5 Combined account risk
`raw = rules_hit_count + max(oddball_z, 0) + max(temporal_score, 0)`; `risk = min(raw / p99(raw), 1)` where `p99` is the 99th percentile of `raw` over all accounts. Each account returns its contributing signals for the explanation panel.

---

## 9. Cash-out prediction (`predict/`)

**Prediction unit:** for a given fraud case at its prediction time (Section 7.3), rank **ATMs** by probability that the case's money is withdrawn there within the next 2h / 6h / 24h. The heatmap renders these ATM probabilities as heat.

"Chain-linked accounts" below = the accounts returned by `trace_case` for the case, plus their direct neighbours. Never the network's ground-truth membership.

### 9.1 Three models (all must be selectable in the UI)

| Model | Logic |
|---|---|
| Baseline | Rank ATMs by how recently chain-linked accounts last withdrew there. Probability from a simple recency decay. |
| KDE | `sklearn.neighbors.KernelDensity` over past withdrawal coordinates by chain-linked accounts; score each ATM by density. Tune bandwidth on training days. If there are no past withdrawals, fall back to the baseline and say so in the reasons. |
| Graph-aware XGBoost | Binary classifier per (case, ATM) pair. Features below. |

**XGBoost features per (case, ATM):**
- distance from ATM to the chain's L2 accounts' home districts
- count of past withdrawals at this ATM by chain-linked accounts (last 7 / 30 days)
- KDE density at the ATM
- hops from victim to the account currently holding the money
- temporal burst score of chain accounts (0 when not computed)
- hour of day and day of week of the prediction time
- whether the ATM's district differs from the district chain-linked accounts last withdrew in (captures `hop_district`)

### 9.2 Evaluation (`predict/evaluate.py`)
- **Time-based split:** train on cases whose prediction time falls in days 1–70, test on days 71–90. **Never a random split.**
- Build test cases from every fraud in days 71–90. Labels come from ground truth: the case's withdrawals (`fraud_id`) in each window after prediction time.
- **Headline metric: hit rate** — share of cases where at least one of the case's actual cash-out ATMs is in the top 5, per time window, with the number of cases `n` and a 95% bootstrap interval.
- Secondary: **Precision@5** (share of the top-5 ATMs where a case withdrawal occurred in the window). Show its ceiling next to it: a case that uses one ATM can score at most 0.2, so P@5 is not comparable across strategies.
- Report metrics overall and per strategy. With about 7 frauds a week the test set is only ~20 cases; show `n` everywhere a metric appears.
- Always report the baseline beside the other models. Expose results via API for the UI.
- If the graph-aware model does not beat the baseline, say so in the output — do not tune the test set to make it win. (With a fixed 3-ATM pool, the baseline is expected to be strong on `rotate_near_collector`.)

### 9.3 Explanations
Every ATM prediction returns its top 3 reasons in plain language, e.g. "Accounts in this chain withdrew here 4 times in 30 days", "Money is 1 hop from cash-out", "Accounts in this chain usually cash out in a different district from last time". Use XGBoost feature contributions (`pred_contribs=True`) mapped to templated sentences. Reasons describe chain-linked accounts — never "the network", whose membership is hidden ground truth.

---

## 10. Fund blocking (`block/`)

**Goal:** recommend the **fewest** accounts to freeze that stop the most money reaching cash-out.

**Method — node-capacity min-cut:**
1. Take the traced case subgraph as of the demo clock.
2. Add a super-source `S` → victim account (infinite capacity) and every L2 / withdrawing account → super-sink `T` (infinite capacity).
3. Freezing acts on **accounts (nodes)**, but min-cut cuts **edges**. Convert with **node splitting**: replace each account `v` with `v_in → v_out`; original edges run `u_out → v_in` with infinite capacity. The victim, `S`, and `T` are not split.
4. **Node capacity counts accounts, not money:** `cap(v) = 1 − 0.01 × (money through v / case amount)`. The cut therefore minimises the number of accounts; among cuts of equal size, it prefers the accounts carrying more money. Accounts the money has already fully left by the demo clock get infinite capacity — freezing them stops nothing.
5. `networkx.minimum_cut(G, 'S', 'T')` → the cut's `v_in → v_out` edges are the accounts to freeze.
6. If the cut has more than `k` accounts (default `k = 3`), fall back to greedy: repeatedly freeze the account whose removal most reduces the money reachable (below).

**Simulate freeze:** money reachable = max flow from victim to `T` over the case subgraph with edge capacity = transaction amount, excluding money already withdrawn by the demo clock. Remove the chosen accounts and recompute. Return money reachable **before** and **after**, and the share stopped.

**Tests:** on a hand-built graph with an obvious single chokepoint, the recommender returns that chokepoint. On the demo case: with the demo clock set before the collector forwards, it recommends the collector (1 account), not the 3 L1 mules or the 2 L2 accounts; at story step 6 (money already in L2) it recommends the 2 L2 accounts, because the collector no longer holds anything. An account the money has already left is never recommended.

---

## 11. Adversary (`adversary/`)

A simulated criminal changes cash-out behaviour to avoid the predicted top-5 ATMs.

**Detected** = at least one of the case's cash-out ATMs is in the model's top 5 for the **6h window** (the adversary's target window).

**Moves and costs (all in ₹, so moves are comparable):**

| Move | Effect | Cost |
|---|---|---|
| Switch ATM | Withdraw at an ATM outside the top-5 | ₹500 + travel (₹10/km) |
| Delay | Wait 12h before withdrawing | Expected freeze loss: `amount held × (1 − (1 − p)^12)`, `p = freeze_risk_per_hour` |
| Add mule hop | Insert one extra layer | ₹3,000 (mule's cut) + 1 hour |
| Split amount | Split across 2 more ATMs | ₹1,000 per extra ATM |

After each move the case's prediction is recomputed.

**Greedy search:** from a case, repeatedly apply the move with the largest drop in detection probability per ₹ of cost, **with no budget cap**, until the case is undetected or no move lowers the probability. Record the cumulative cost after each move.

**Evasion cost curve:** for budgets ₹0–₹25,000 in steps, a case counts as detected at budget `b` if it is still detected after the last move whose cumulative cost ≤ `b`. Detection rate over the test cases vs. budget is then non-increasing by construction. Plot detection rate vs. budget.

**Hardening:** retrain XGBoost with training data augmented by adversary-generated cash-outs **from training-period cases only** (days 1–70); recompute the curve on the test cases. The UI shows both curves.

Every move is logged for the Adversary Lab screen.

---

## 12. Build phases

**Current status:** Phases 2, 3, and 4 implemented; see `docs/phase-2.md`,
`docs/phase-3.md`, and `docs/phase-4.md` for checks, limitations, and results.
The next phase is Phase 5, after review.

Build in order. Each phase ends with its checks passing and a short summary. **Stop after each phase.**

### Phase 0 — Scaffold
- Repo structure, `run.sh` + `run.ps1`, FastAPI `/health`, precompute-cache skeleton (`python -m app.precompute`, cache keyed by a hash of the scenario file, loaded at startup), React app shell with sidebar (6 screen stubs, Section 14), top bar with persona switcher and notification bell, "Simulated data" badge, dark theme, `lib/format.ts` (₹ in lakh/crore style, IST).
- **Check:** `.\run.ps1` (and `./run.sh` in Git Bash) starts both; all 6 screens reachable; `format.ts` unit tests pass.

### Phase 1 — Scenario + simulator
- Scenario loader, agents, event queue, model, runner, demo clock, ground truth export, `/districts`.
- **Check:** pytest — determinism, per-network topology + transfer style + cash-out strategy, demo case path, complaint for every fraud.

### Phase 2 — Graph + detection + Case View + Command Center
- Graph builder, `trace_case`, rules, OddBall, temporal, combined risk.
- Command Center: KPI strip, complaint feed, mini map.
- Case View: Cytoscape graph left to right, role colours, "Play" animation, side panel with pattern and signals, clickable nodes.
- **Check:** demo case traces with the configured path; its chain is labelled mule fan-in (collector) + layering; each rule fires on its expected accounts (Section 8.2 table) and fan-in does not fire on merchants.

### Phase 3 — Prediction + Risk Heatmap
- Three models, evaluation, explanations. Precomputed into the cache.
- Heatmap: district polygons, ATM points, heat by probability, time-window and threshold filters, model switcher, explanation card.
- **Check:** evaluation table printed with baseline beside others, `n` and intervals shown, per strategy; a leakage test proves no prediction reads a record after its prediction time; heatmap renders offline.

### Phase 4 — Alerts + Fund Blocking
- Alert generation when an ATM crosses the threshold; mock delivery log (SMS/email/API) on the Alerts screen; alert statuses.
- Fund Blocking screen: ranked recommendations, before/after bar, "Simulate freeze".
- **Check:** min-cut tests pass (Section 10); demo case shows money reachable dropping after freeze.

### Phase 5 — Adversary Lab
- Moves, greedy search, evasion cost curves (baseline vs hardened), move log, toggle.
- **Check:** the curve is non-increasing in detection rate as budget rises; hardening uses no test-period cases.

### Phase 6 — Demo polish
- **Demo script mode:** a "Start demo" button that injects the complaint and walks the 7 steps with "Next" prompts, advancing the demo clock.
- **Reset** button (< 5 s) restoring the initial state from the in-memory snapshot — never by recomputing.
- Offline verification (no network requests at runtime), projector-readable sizes (≥ 14 px body), 1080p layout.
- **Check:** full story completes three times in a row with resets between; cold start from an existing cache is under 10 s.

---

## 13. API endpoints

| Method | Path | Returns |
|---|---|---|
| GET | `/health` | status |
| GET | `/summary` | KPI strip values |
| GET | `/complaints` | complaint feed |
| POST | `/demo/start` | injects the scripted complaint, starts the demo clock |
| POST | `/demo/next` | advances the demo clock to the next story step |
| POST | `/demo/reset` | restores initial state |
| GET | `/cases/{complaint_id}/trace` | nodes, edges, hop order, detected patterns |
| GET | `/accounts/{id}` | account details, signals, source transactions |
| GET | `/districts` | GeoJSON |
| GET | `/atms` | ATM list |
| GET | `/predictions/{complaint_id}?model=&window=` | ranked ATMs with probability and reasons |
| GET | `/evaluation` | metrics per model per window, with `n` and intervals |
| GET | `/alerts` / POST `/alerts/{id}/ack` | alert list / acknowledge |
| GET | `/block/{complaint_id}` | freeze recommendations |
| POST | `/block/{complaint_id}/simulate` | before/after money reachable |
| POST | `/adversary/run` | move log + detection result |
| GET | `/adversary/curves` | evasion cost curves |

---

## 14. UI rules

**The 6 screens:** Command Center · Case View · Risk Heatmap · Alerts · Fund Blocking · Adversary Lab.

- Dark control-room theme; high contrast for projectors.
- Predicted items look different from observed ones: **dashed lines, lighter fill**.
- Every score has an adjacent "Why?" that opens its reasons and source records.
- ₹ amounts in Indian format (₹50,000 · ₹1.2 lakh · ₹3.4 crore); times in IST.
- Loading states never blank the screen; data is precomputed.
- Persona switcher (I4C / Investigator / Bank officer) changes the default screen and which actions are highlighted — no real auth.
- Metrics always show their sample size `n`.

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
- Precompute is expensive (simulation + training + adversary curves). Build it once into `backend/.cache/<scenario-hash>/`; startup loads the cache and only rebuilds when the scenario file changes.
- The dev machine is Windows: test both run scripts; when starting servers from a tool shell, detach them from the console so they survive the shell exiting.

---

## 17. Changes from v1 (2026-09-29)

| # | v1 problem | v2 decision |
|---|---|---|
| 1 | Fan-in needed ≥ 8 senders; collectors only ever get 3–4, so the Phase 2 check could never pass | ≥ 3 senders in 6h, forwarded ≥ 90% in 24h, repeated ≥ 2 times; merchants added as hard negatives |
| 2 | Layering needed 5 accounts, < 30 min hops, 92–98% per hop; demo path has 4 accounts, mules take up to 45 min, collector pools | ≥ 4 accounts, < 3h per hop, 85–98% on summed in/out flows |
| 3 | Structuring, scatter, burst had no simulated behaviour to detect | `transfer_style` per network: N_B structured, N_C scatter (N_C L2 raised to 6); expected burst coverage documented |
| 4 | Victim → "a" L1 mule contradicted the demo's 3 L1s; `mule_l3` unused; L1 target unclear | Victim splits to 1–3 L1s; fixed topology victim → L1 → collector → L2; L3 removed |
| 5 | Hourly `step()` vs minute-level behaviour | Event queue (Section 7.2) |
| 6 | No clock: predictions could see the demo case's own withdrawals | Demo clock + prediction time rule (Section 7.3), leakage test |
| 7 | Min-cut on money picked 2 L2s over the single collector; could recommend accounts money had already left | Unit capacity with money tiebreak; already-passed accounts uncuttable; demo tests expect the collector before it forwards and the 2 L2s at step 6 |
| 8 | Delay cost in hours, not ₹; "detected" undefined for splits | Delay priced as expected freeze loss; detected = any cash-out ATM in 6h top-5 |
| 9 | Budgeted greedy could make the curve non-monotone | Uncapped greedy, curve read off cumulative cost |
| 10 | Hardening could train on test cases | Training-period cases only |
| 11 | ~20 test cases, P@5 ceiling of 0.2 on single-ATM cases | Hit rate headline with `n` + bootstrap CI; P@5 secondary with ceiling shown; per-strategy breakdown |
| 12 | Explanations referred to "the network" (hidden ground truth) | Reasons phrased over chain-linked accounts |
| 13 | Risk "normalised to 0–1" unspecified | Divide by p99, clip at 1 |
| 14 | "6 screens" never named | Named in Section 14 (Alerts is its own screen) |
| 15 | `./run.sh` only; demo laptop is Windows | `run.ps1` added as primary |
| 16 | Full precompute on every start conflicts with "< 2 s" and "reset < 5 s" | Disk cache keyed by scenario hash; reset from in-memory snapshot |
| 17 | Two copies of district shapes | `/districts` from the scenario is the only source |
| 18 | Offline pitfalls | `CircleMarker`, `cytoscape-dagre` noted, system fonts only |
| 19 | Complaint had no fraud time for `trace_case` | `Complaint.incident_at`; every fraud generates a complaint |
| 20 | (Phase 1) Mesa vs plain loop | Plain-Python hourly loop, allowed by §3: all timed behaviour goes through the event queue, and this keeps runs fully deterministic. Fraud-chain agents are reactive (`on_receive`); their `step()` is a no-op. |
| 21 | (Phase 1) Collector's first payment came 1-100 min after the 20-90 min payout time | The first payment leaves exactly at the payout time, so "forwards 20-90 min after the last L1 forward arrives" holds (found by the Phase 1 tests) |
| 22 | (Phase 1) No balances | Account balances are not modelled; the simulator guarantees only the flows described in §7 |
| 23 | (Phase 1) `collector_district` missing from the scenario shape | Added per network (§6) so "near the collector's district" is defined by data, not by code |
