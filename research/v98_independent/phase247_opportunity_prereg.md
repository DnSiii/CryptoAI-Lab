# V98 Independent Phase247 — Synchronized Breakout Opportunity Sleeve

Status: PREREGISTERED BEFORE PHASE247 PNL.

## Architecture role
Growth Core primitive is the frozen Clean-4 structural beta reference from Phase245/246 (+0.25 BTC/ETH/BNB/SOL, gross 1.0). Phase247 adds a small **Opportunity Sleeve** only during synchronized upside expansion. It does not replace the core and does not reuse the rejected Phase244 persistent 90d/30d channel state.

## Frozen hypothesis
A rare market-wide closing-high breadth event identifies periods where accepting a modest temporary increase in gross can add convex wealth on top of structural beta.

At each 23:00 UTC close(t):
1. For each Clean-4 asset, compute the maximum close over the previous 30 calendar days / 720 hours, excluding close(t).
2. An asset has an upside breakout if close(t) > that prior 30d maximum.
3. Opportunity ON iff at least **3 of 4** Clean-4 assets break out simultaneously.
4. Sleeve target when ON = +0.0625 in each asset = +0.25 gross.
5. Sleeve target when OFF = zero.
6. Core target remains +0.25 each continuously from first 2023 open.
7. Combined target = +0.3125 each when opportunity ON (gross 1.25), otherwise +0.25 each (gross 1.0).
8. Decision at 23:00 close executes next 00:00 open. Reassess once daily; an event may renew while the condition remains true.

No short side, leverage above 1.25, threshold/window grid, hold-period search, vol filter, stop, regime filter, asset subset, or post-result rescue.

This is distinct from Phase244: Phase244 was a standalone persistent per-asset 90d entry/30d exit long/short state machine. Phase247 is a market-wide one-day marginal overlay on an always-long structural core, using 30d synchronized breadth and no persistent per-asset state.

## Frozen data / execution
Authenticated Phase243 Clean-4 only; Dec-2022 warmup through 2025-12; native PIT funding; XRP quarantined. No 2026+, V14/V15/V99.

Existing V98 costs/funding:
- BASE 7bp, funding 1/1
- SEVERE 12bp, 1.25/.75
- SUPERSEVERE 20bp, 1.75/.50
Combined open-gross cap = 1.25.

## Frozen comparator
Exact structural Clean-4 core under the same backtester and all three cost/funding tiers.

## Opportunity promotion gate
Phase247 becomes **OPPORTUNITY_SLEEVE_CANDIDATE** only if:
1. BASE combined return > core BASE return by at least 5% relative: combined_return > core_return * 1.05.
2. BASE combined CAGR > core CAGR.
3. BASE max DD is not worse than core max DD by more than 5 percentage points.
4. BASE daily PF >= 1.10.
5. BASE worst day >= -20%.
6. Marginal combined-vs-core calendar return is positive in at least 2/3 folds.
7. No calendar fold underperforms core by more than 10 percentage points.
8. SEVERE combined return > core SEVERE return.
9. SUPERSEVERE combined return > core SUPERSEVERE return.
10. No ruin; max open gross <=1.250000001.
11. Max asset contribution share <=70%.
12. Top-10 absolute daily-return concentration <=45%.

Failure => REJECT_OPPORTUNITY_NO_RESCUE for this exact 30d / breadth-3 / +0.25 gross sleeve. No validation/holdout.
