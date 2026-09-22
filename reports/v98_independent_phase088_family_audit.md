# V98 Independent Phase088 — Hypothesis-family audit

Status: **AUDIT_COMPLETE / NO_ALPHA_EXECUTED**.

This audit is selection hygiene after Phase087 and before any new PnL. It uses only V98 Independent artifacts on `research/v98-independent-zero`. It does not use V99 evidence and does not reinterpret the opened Phase083 holdout.

## Holdout discipline

Phase083 (2026-08-01 through 2026-09-15) has been opened once and is permanently ineligible for future V98 selection, tuning, rescue, sign choice, threshold choice, or mechanism ranking. A future final gate requires a genuinely new forward untouched window accumulated after the next candidate is frozen.

## Mechanism families already consumed

The accumulated V98 artifact namespace shows extensive coverage of: residual momentum/reversal/quality/trend/autocorrelation/tails; cross-sectional dispersion and low-volatility/downside structure; beta stability/asymmetry/convexity and BTC lead/market decoupling; OHLC range/wick/close-location/channel/trend-efficiency/sign entropy/sign streak; volume attention/signed pressure/divergence/trade size/intensity/concentration; volatility compression/vol-of-vol/downside asymmetry; funding carry/dispersion/shock/interval; open interest, positioning, taker pressure and book depth; spot-perp and COIN-M/USD-M basis; liquidation/options/on-chain/macro/stablecoin/system-liquidity feasibility; calendar/UTC seasonality; and peer/cross-asset correlation/lead-lag.

These families are closed against cosmetic rescue. In particular, changing only sign, lookback, threshold, quantile, cadence, gross, symbol subset, regime mask, cost assumption, neutralization detail, or combining rejected mechanisms does not constitute a new independent hypothesis.

## Evidence-based gap

A materially distinct price-path property not represented by the executed filenames/mechanisms is **cross-sectional overnight-gap / session-boundary continuation versus intraday reversal**. The economic mechanism is discontinuous repricing at the UTC daily boundary rather than trend magnitude, candle location, wick geometry, UTC-block seasonality, or volume/range concentration. It can be defined from already-authorized OHLC data without requiring a new provider and can be made strictly causal using only the prior completed day's open/close and the current rebalance boundary.

However, after 80+ V98 attempts and one opened final holdout, another immediate PnL experiment has a high multiple-testing burden. Phase088 therefore stops at the audit and does **not** inspect alpha. The next experiment must first preregister the exact session-boundary statistic, causal timing, neutralization, fixed lookback (if any), cost/funding model, folds, BASE/severe/supersevere gates, concentration/tails, and the policy for a new future untouched final window.

## Decision

**PASS_AUDIT_ONLY.** No champion exists. Phase087 remains REJECT_NO_RESCUE. Phase083 remains permanently opened/ineligible. Validation stays closed until a new preregistered training candidate passes. Recommended next independent family: session-boundary gap continuation/reversal, subject to a separate preregistration before any PnL.
