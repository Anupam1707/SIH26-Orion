# Phase 3 — Cash-out prediction

MuleTrail now returns an ATM ranking for each visible complaint, three horizons
(2, 6, and 24 hours), and three selectable methods: recency baseline, spatial
kernel density, and graph-aware XGBoost. The Risk Heatmap draws the scenario's
districts without map tiles, shows predicted ATM probabilities as dashed circles,
and links each of its three reasons to its source group. Users can filter the
ranking by minimum probability, inspect an ATM, and read the case-level evaluation.

## Training and evaluation

- Public feature extraction receives only the clock-limited data view. It derives
  the observed transfer trace and direct neighbours; ground-truth IDs, membership,
  strategy, and cash-out outcomes cannot reach model inputs.
- Each case gets its own expanding-history fit using earlier cases with completed
  24-hour outcomes. The holdout cases (prediction times on days 71–90) share the
  model and KDE bandwidth frozen on completed training outcomes available by day 70.
  Incomplete training outcomes are censored for fitting. No model sees a label after
  the time at which it becomes available.
- A case's own withdrawals occur after its prediction time, checked during case
  construction. Features, withdrawal coordinates, and evidence records are cut off
  at that prediction time. The API withholds predictions until both their complaint
  and prediction time are visible on the demo clock.
- Recency and KDE rank weights are scaled by completed training-case cash-out rates
  for each horizon. These are explicitly heuristic marginal estimates. XGBoost is
  a separate binary model for each horizon; its probability is not calibrated, and
  estimates are not guaranteed to increase with the forecast window. Cold starts
  and one-class training data report their baseline fallback in the response.
- KDE uses an equirectangular kilometre projection and a deterministic bandwidth
  search over prequential scores on training cases only. The search never uses the
  test cases.
- Evaluation is chronological: training prediction times on days 1–70, test times
  on days 71–90. The headline is top-5 hit rate, bootstrapped by case with a 95%
  interval. Precision@5 shows its case-specific ceiling. No-cash-out cases count as
  misses, and cases without a fully observed 24-hour outcome at the current clock
  are reported as pending. Results appear for each strategy and overall; baseline
  comparisons explicitly say when XGBoost loses.
- The fixed-seed held-out run has 17 cases. At 6 hours the overall hit rates are
  11.8% baseline, 29.4% KDE, and 41.2% XGBoost. XGBoost loses to baseline for
  `hop_district` at 6 and 24 hours (n=5) and does not win on the 2-hour overall
  window (n=17). These small samples and intervals stay visible in the UI; the test
  set was not tuned.

## Files and outputs

`backend/app/predict/` owns case-label isolation, feature extraction, the three
models, reason templates, rolling-origin fitting, and evaluation. The precompute
cache contains predictions, metric snapshots for clock states, three XGBoost model
files where both classes exist, and a printed evaluation table. `GET /atms`,
`GET /prediction-cases`, `GET /predictions/{complaint_id}`, and `GET /evaluation`
serve clock-filtered outputs. The Risk Heatmap lives at `/heatmap`.

## Check and known limitations

Backend regression checks cover held-out dates, completed-label cutoffs, mutations
to future and hidden records, stable bootstrap results, a KDE no-history case,
probabilities, XGBoost repeatability/contributions, API clock gates, model fallbacks,
and explanation records. Frontend checks cover the production build, threshold
filtering, record links, and the three reason-source groups.

The prediction report is a seeded simulation, not an estimate of real-world bank
performance. Holdout n is small. The heat circles show probabilities at ATM points,
not a continuous calibrated district surface. Visual browser and runtime network
verification could not be completed in this turn.
