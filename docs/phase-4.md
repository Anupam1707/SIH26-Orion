# Phase 4 — Alerts + Fund Blocking

## What changed

### Backend — New modules

| Module | Purpose |
|---|---|
| `app/block/mincut.py` | Node-capacity min-cut algorithm (spec §10). Node splitting converts account freezing into edge-cut. Greedy fallback when cut exceeds k accounts. |
| `app/block/service.py` | Service layer bridging trace data with min-cut. Enriches recommendations with account details. |
| `app/alerts/service.py` | Alert generation from precomputed predictions. Threshold-based triggers, severity classification, mock delivery channels (SMS/email/API). |
| `app/api/alerts.py` | Router: `GET /alerts`, `POST /alerts/{id}/ack`, `POST /alerts/generate/{complaint_id}` |
| `app/api/blocking.py` | Router: `GET /block/{complaint_id}`, `POST /block/{complaint_id}/simulate` |
| `tests/test_blocking.py` | 6 tests: hand-built chokepoint, money drops after freeze, already-withdrawn accounts, simulate freeze, demo case integration |
| `tests/test_alerts.py` | 8 tests: threshold triggers, severity levels, channels, state management, acknowledgement |

### Backend — Modified files

| File | Change |
|---|---|
| `app/main.py` | Registered `alerts` and `blocking` routers |

### Frontend — New screens

| Screen | Route | Features |
|---|---|---|
| Alerts | `/alerts` | Alert feed with severity badges, case filtering, mock delivery log (SMS/email/API), alert acknowledgement, KPI strip (total/triggered/acknowledged) |
| Fund Blocking | `/blocking` | Min-cut recommendations with selectable accounts, before/after money-reachable bars with animated transitions, simulate freeze button |

### Frontend — Modified files

| File | Change |
|---|---|
| `api/client.ts` | Added 5 API methods + 6 TypeScript interfaces for alerts and blocking |
| `App.tsx` | Wired Alerts and FundBlocking screens into routes; live alert count in TopBar notification bell |
| `index.css` | 55 new CSS rules for alert and blocking layouts |

## API endpoints added

| Method | Path | Description |
|---|---|---|
| `GET` | `/alerts` | List all alerts created up to the demo clock |
| `POST` | `/alerts/{id}/ack` | Acknowledge an alert |
| `POST` | `/alerts/generate/{complaint_id}` | Generate alerts from precomputed predictions |
| `GET` | `/block/{complaint_id}` | Freeze recommendations via min-cut |
| `POST` | `/block/{complaint_id}/simulate` | Simulate freezing specific accounts |

## Algorithm: Node-Capacity Min-Cut

The fund blocking algorithm follows spec §10:

1. Takes the traced case subgraph at the current demo clock
2. Adds super-source `S` → victim (∞ capacity), terminal accounts → super-sink `T` (∞)
3. Splits each account `v` into `v_in` → `v_out` with capacity `1 − 0.01 × (money_through_v / case_amount)`
4. Accounts whose money has already left get infinite capacity (cutting them stops nothing)
5. `networkx.minimum_cut(G, S, T)` → cut `v_in → v_out` edges = accounts to freeze
6. Greedy fallback when cut exceeds k=3 accounts

The simulate-freeze path uses a separate amount-based flow graph to compute realistic before/after money metrics.

## Checks (spec Phase 4)

- [x] Min-cut tests pass (hand-built chokepoint graph returns single chokepoint)
- [x] Demo case: money reachable drops after freezing recommended accounts
- [x] Already-withdrawn accounts not recommended (infinite capacity)
- [x] Simulate freeze shows before/after money flow change
- [x] Alert generation fires on threshold crossing
- [x] Alert acknowledgement updates status
- [x] All 50 backend tests pass (14 new + 36 existing)
- [x] TypeScript compiles clean (0 errors)
- [x] Frontend builds successfully

## Limitations

- Alerts are generated on-demand (via the generate button or API call), not automatically during demo advance. This will be wired into the demo script in Phase 6.
- The pre-existing `test_prediction.py` has a DLL load failure for `sklearn._liblinear` due to the machine's Application Control policy — this is not related to Phase 4 changes.
