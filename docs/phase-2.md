# Phase 2 — Graph and investigation

Implemented the observed transaction multigraph, chronological case tracing, five
typology rules, OddBall, temporal burst scores, and combined account risk. The
Command Center now shows clock-filtered KPIs, a complaint feed, and a tile-free
district map. Case View has a left-to-right Cytoscape graph, hop playback, account
selection (including keyboard-accessible buttons), and expandable evidence tables.

## Try it

Run `.\run.ps1` from PowerShell (or `./run.sh` in Git Bash), then open
`http://127.0.0.1:5173`. Choose **Open demo trace** in Command Center. This Phase 2
preview advances to the completed transfer chain, before cash-out. Select the
collector to inspect fan-in and layering evidence. **All complaints** returns to
Command Center; **Reset history** restores the initial clock without recomputing.
The guided seven-step story remains Phase 6 work.

## Implementation decisions

- Detection and tracing only consume the public, clock-filtered data view. Hidden
  roles and fraud identifiers are removed before analysis. The precompute module
  uses scenario truth only to schedule the demo preview clock.
- Detection results are cached for the history and preview clocks. API startup
  loads those snapshots and builds the corresponding immutable graphs. Changing
  the scenario or cache format version invalidates the cache.
- Tracing is a conservative chronological flow attribution, not proof of fund
  ownership: outgoing transfers consume traced receipts, including pruned small
  branches, and cannot spend more traced funds than have arrived. Roles are
  inferred from rules; terminal recipients are not asserted to be known mules.
- Fan-in includes a conservative receipt-coverage guard. A six-hour receipt slice
  cannot claim an ordinary payment against a larger pool of receipts as forwarding.
  It requires the outgoing total to cover at least the configured forwarding share
  of observed receipts in the surrounding settlement window (24 hours either side
  of the candidate start, clipped at the demo clock). This reduces recall for
  overlapping cases but prevents the simulator's merchants from triggering fan-in.
  All receipts used by the guard are included in its evidence.
- Repetition counts use non-overlapping episodes. Layering sums pooled receipts and
  split outflows before linking consecutive intermediaries; no hidden membership is
  used. Signals indicate observed patterns, not a determination of criminality.
- The frontend uses Cytoscape directly within a React lifecycle so listeners,
  resize observation, and animation timers are cleaned up on case changes.

## Verification

Backend checks cover all planted rule types, merchant fan-in negatives, the exact
seven-node/eight-edge demo trace, source records, future-record and hidden-label
invariance, temporal zero-variance handling, trace conservation and chronology,
preview/reset, and API response time. Frontend validation covers strict TypeScript,
the production build, and the existing currency/time formatting tests.

Visual browser verification remains outstanding: this execution environment
exposed no connected browsers. The map has no tile layer, fonts are local system
fonts, and assets are bundled; a runtime network audit is still a Phase 6 check.

Phase 3 (prediction models, evaluation, and Risk Heatmap) has not been started.
