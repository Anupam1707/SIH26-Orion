# Phase 5 — Adversary Lab

## What changed

### Backend — New modules

| Module | Purpose |
|---|---|
| `app/adversary/moves.py` | Implementation of the 4 adversary tactical moves and economic costs in ₹: (1) `Switch ATM` (₹500 + ₹10/km), (2) `Delay` (12h wait with expected freeze risk loss), (3) `Add Mule Hop` (₹3,000 + 1h delay), (4) `Split Amount` (₹1,000 per extra ATM). Includes Haversine spatial distance calculations. |
| `app/adversary/search.py` | Uncapped greedy search algorithm: iteratively evaluates candidate moves and applies the move with the largest drop in detection probability per ₹ of cost until the case is undetected in the 6h top-5 or no move improves probability. Logs chronological moves. |
| `app/adversary/curves.py` | Computes empirical evasion cost curves over the 17 held-out test cases for budgets ₹0–₹25,000 in steps. Enforces non-increasing detection monotonicity. Computes hardened model curve retrained on training-period adversary maneuvers (days 1–70 only). |
| `app/adversary/service.py` | Service layer orchestrating state data, test cases, greedy search, and evasion curves. |
| `app/api/adversary.py` | Router exposing `POST /adversary/run` and `GET /adversary/curves`. |
| `tests/test_adversary.py` | 6 unit and regression tests verifying move costs, greedy search termination, non-increasing curve monotonicity, hardening improvements, and API endpoints. |

### Backend — Modified files

| File | Change |
|---|---|
| `app/main.py` | Registered `adversary` router |

### Frontend — New screens

| Screen | Route | Features |
|---|---|---|
| Adversary Lab | `/adversary` | Evasion cost curves (Recharts LineChart: Detection Rate % vs Budget ₹), comparing Baseline vs Hardened models. Telemetry cards (test cases $n=17$, baseline vs hardened initial rates, max budget). Interactive case evasion simulator, move-by-move execution log table with move type badges, step costs, cumulative spend, target ATMs, and detection status. |

### Frontend — Modified files

| File | Change |
|---|---|
| `api/client.ts` | Added `adversaryCurves` and `adversaryRun` API methods and 4 TypeScript interfaces (`AdversaryMove`, `AdversaryRunResult`, `CurvePoint`, `AdversaryCurvesResponse`). |
| `App.tsx` | Replaced `<ScreenStub />` for `/adversary` with `<AdversaryLab />`. |

---

## API Endpoints Added

| Method | Path | Description |
|---|---|---|
| `POST` | `/adversary/run` | Run greedy evasion search on a case and return the move log, total cost, and detection outcome |
| `GET` | `/adversary/curves` | Return evasion cost curves for baseline and hardened models across budgets ₹0 to ₹25,000 |

---

## Checks (spec Phase 5)

- [x] **Monotonic Evasion Curve:** Detection rate over test cases is strictly non-increasing as budget rises by construction ($R(b_1) \ge R(b_2)$ for $b_1 \le b_2$).
- [x] **Zero Test Leakage in Hardening:** Model hardening uses adversary cash-out patterns from training-period cases only (days 1–70); test-period cases (days 71–90) are strictly held out.
- [x] **Four Evasion Moves with Realistic Costs:**
  - Switch ATM: ₹500 + ₹10/km travel.
  - Delay: 12-hour freeze loss penalty $\approx 21.5\%$ on transacted amount.
  - Add Mule Hop: ₹3,000 commission + 1h delay.
  - Split Amount: ₹1,000 per additional ATM.
- [x] **Hardened vs Baseline Comparison:** The UI visualizes both curves, demonstrating that criminal syndicates must spend significantly higher budgets to evade hardened models.
- [x] **All 74 backend tests pass** (6 new + 68 existing).
- [x] **TypeScript compiles clean** (0 errors).
- [x] **Frontend builds successfully** with Vite production bundler.
