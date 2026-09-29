# V99 R106 — Phase180 arrival-source decision

Date: 2026-09-29
Status: REJECTED AT DATA GATE (no PnL inspected)

## Evidence harvested
The deterministic observer audit completed successfully at the workflow level but no observer passed the preregistered full-TRAIN coverage gate.

TRAIN interval: `[2021-12-01T00:00:00Z, 2024-01-18T00:00:00Z)`.

Observer results:
- cairn: FAIL — 6,648 rows; coverage 2021-12-03 04:00:00Z to 2021-12-21 14:50:00Z; 27 distinct days.
- stadicus: FAIL — 3,712 rows; coverage 2021-12-03 04:00:00Z to 2021-12-13 11:10:00Z; 19 distinct days.
- bitnodes: FAIL — 1,830 rows; coverage 2021-12-03 04:00:00Z to 2021-12-08 06:10:00Z; 12 distinct days.
- dsnode: FAIL — 1,581 rows; coverage 2021-12-03 04:00:00Z to 2021-12-07 13:20:00Z; 11 distinct days.
- localhost: FAIL — 0 rows.

Upstream source was pinned to commit `1bb1c1b7c740455ed0a4335e10f072ec5403e528`; audit output was produced deterministically by the Phase180 source-audit workflow.

## Independent failure audit
This is not a marginal gap problem. Every non-empty observer terminates in December 2021, roughly two years before the TRAIN cutoff. Therefore:
1. no single fixed observer provides the required historical point-in-time arrival timestamps;
2. stitching observers cannot repair the missing 2022–2024 interval and would introduce observer-selection degrees of freedom;
3. falling back to miner-declared `header.time`, inferred offsets, earliest-of-observers, interpolation, or market-price alignment would violate the preregistered causal availability requirement;
4. inspecting alpha/PnL to choose a workaround would contaminate the DATA gate.

## Decision
Phase180 Block-Production Stress is **REJECTED AT DATA GATE** for V99 R106. No alpha, PnL, benchmark, regime, cost, or holdout result may be used to revisit this decision.

The block-header integrity and feature tooling remain useful infrastructure, but Phase180 is not admissible as a V99 candidate unless a genuinely new, independently sourced, fixed-observer historical arrival dataset covering the complete TRAIN interval is discovered in a future research branch and passes the existing gate unchanged.

## Preserved invariants
- V16 Frozen: untouched.
- V99 Frozen: untouched.
- Holdout: untouched.
- causal t-1: preserved.
- chronological train-only selection: preserved.
- temporal folds / severe and supersevere costs / regime matrix / benchmark envelope: not reached because DATA gate failed.
- anti-overfit: fail-closed; no threshold/window/source relaxation.
