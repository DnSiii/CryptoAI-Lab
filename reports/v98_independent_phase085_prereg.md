# V98 Independent Phase085 — Intraday Volume-Concentration Spread (PREREGISTRATION)

Status: FROZEN BEFORE ANY PHASE085 PNL INSPECTION.

## Independence / selection hygiene
Phase084 is rejected without rescue because its frozen training gate failed (2025 return/PF and both stress returns). Phase085 is a new mechanism and does not alter Phase084. It does not use Phase083 holdout outcomes, V99, V16, validation, or any future holdout for selection. The already-opened 2026-08-01..2026-09-15 Phase083 window is permanently forbidden as an untouched holdout for this or later candidates.

## Hypothesis
Persistent concentration of an asset's completed-day trading activity into a small subset of hours may proxy scheduled/structural participation rather than directional price momentum. For each symbol and completed UTC day, compute hourly quote-volume shares across the 24 completed hours and Herfindahl concentration HHI = sum(share^2). At 00:00 UTC on day t, use only day t-1 HHI. Rank the five frozen symbols cross-sectionally; long the highest-HHI symbol and short the lowest-HHI symbol, equal absolute legs. No return sign, return magnitude, funding signal, V99/V16 output, Phase083 result, or future data enters the score.

## Frozen specification
- Symbols: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT.
- Input: canonical hourly `volume` field already available to V98 training data; if quote-volume is not separately available, use the canonical volume field exactly as stored, with no price-derived substitution after results.
- Score: completed prior UTC day's 24 hourly volumes; nonnegative finite values only; HHI = sum((v_i / sum(v))^2). Require positive daily volume and at least 20 finite hourly observations; otherwise that symbol is unavailable that day.
- Rebalance: 00:00 UTC daily; positions persist until next rebalance.
- Ranking: deterministic `(score, symbol)` ordering.
- Portfolio: long highest HHI +0.375, short lowest HHI -0.375; gross cap 0.75. Require at least two available symbols and distinct scores; otherwise flat.
- Training only: frozen chronological training through 2025-12-31 using existing V98 training configuration. No Phase083 interval is read for selection.
- Costs/funding: existing V98 BASE, severe and supersevere cost/funding definitions unchanged.

## Frozen training gate
ALL must pass: aggregate return > 0; daily PF > 1.05; max drawdown >= -35%; no ruin; every chronological fold return > 0 and PF > 1.00; severe return > 0; supersevere return > 0. Report payoff, win rate, positive days, regimes, concentration, tails, per-asset contribution proxy and reproducibility hashes regardless of pass/fail.

## Decision rule
Any training-gate failure => `REJECT_NO_RESCUE`; no sign flip, volume transform, HHI variant, lookback, symbol subset, gross, cadence, threshold, regime filter, cost or funding rescue. Validation remains closed. Full pass => freeze exactly this candidate and preregister a separate confirmation stage. A later final candidate requires a genuinely new future untouched holdout; Phase083 cannot be reused.
