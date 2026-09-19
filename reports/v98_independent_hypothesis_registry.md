# V98 Independent — Hypothesis Family Registry

Status: active research-control artifact after Phase040 rejection.

Purpose: prevent renamed repeats, rescue tuning, and pseudo-diversification. This registry is selection hygiene only; it does not inspect validation/final holdout and does not use V99 evidence.

## Executed V98 families

003 dispersion neutral; 004 tail-risk budget; 005 dual sleeve; 006 consensus residual; 007 residual reversal; 008 tail-budgeted dispersion; 009 funding carry neutral; 010 residual low-volatility; 011 volume attention; 012 residual skew; 013 bull dispersion; 014 non-bear dispersion; 015 continuous residual; 016 residual low-volatility follow-up; 017 residual quality; 018 residual quality consistency; 019 residual trend breadth; 020 residual trend low-turnover; 021 downside resilience; 022 residual autocorrelation; 023 beta stability; 024 residual tail shape; 025 liquidity efficiency / lagged price impact per quote-volume; 026 residual trend efficiency; 027 weekday residual seasonality; 028 residual shock recovery; 029 residual trend efficiency follow-up; 030 BTC lead response; 031 market decoupling; 032 beta convexity; 033 beta asymmetry; 034 cross-asset lead-lag; 035 close-location pressure; 036 wick imbalance; 037 UTC block seasonality; 038 signed-volume pressure; 039 volume-price divergence; 040 residual-volatility compression.

## Closed / no-rescue families

The following families are consumed unless a future proposal has a genuinely different economic mechanism and is preregistered before seeing its result: residual dispersion/trend/reversal/quality/low-volatility/tail shape; funding-level carry; volume attention/pressure/divergence; liquidity/price-impact efficiency; calendar/UTC seasonality; BTC beta stability/asymmetry/convexity/lead response; cross-asset lead-lag; OHLC close-location/wick pressure; residual-volatility compression.

Forbidden rescue behavior includes sign inversion after failure, nearby-window search, cadence search, gross/leverage search, threshold search, regime cherry-picking, or combining failed signals merely to manufacture a new phase number.

## Phase041 admission audit — PASSED before result

Phase041 Trade-Size Pressure was admitted only after the overlap audit. Its economic variable is average quote-value per trade (`quote_volume / trades`), a transaction-size/participation-scale measure not used by the prior V98 alpha families. It is not raw volume attention, signed volume, price/volume divergence, or price impact per volume. The canonical data loader independently exposes hourly `trades` and `quote_volume`, allowing deterministic point-in-time lagging.

Frozen before result: long rising 24h-versus-168h median average trade size / short falling trade size; 24h rebalance; 720h BTC beta; gross 0.75; beta/dollar neutral. No sign/window/cadence/gross/threshold/regime search is permitted after the result.

## Gate preservation

Existing chronological folds, base/severe/supersevere costs and funding stress, concentration/tails, max drawdown, PF, payoff, win rate, positive days, beta/dollar neutrality, regimes and reproducibility diagnostics remain unchanged. Validation stays closed unless training passes. Final holdout stays untouched until training and validation pass and a candidate is formally frozen. V99 is excluded from V98 selection.

## Current decision

Phase040 is rejected and no champion exists. Phase041 is preregistered, implemented, covered by future-invariance/gross/rebalance/dollar-neutrality tests, and queued for the isolated V98 workflow. No Phase041 result has been used to alter its specification.
