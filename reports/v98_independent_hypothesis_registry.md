# V98 Independent — Hypothesis Family Registry

Status: active research-control artifact after Phase044 rejection / Phase045 preregistration.

Purpose: prevent renamed repeats, rescue tuning, and pseudo-diversification. This registry is selection hygiene only; it does not inspect validation/final holdout and does not use V99 evidence.

## Executed V98 families

003 dispersion neutral; 004 tail-risk budget; 005 dual sleeve; 006 consensus residual; 007 residual reversal; 008 tail-budgeted dispersion; 009 funding carry neutral; 010 residual low-volatility; 011 volume attention; 012 residual skew; 013 bull dispersion; 014 non-bear dispersion; 015 continuous residual; 016 residual low-volatility follow-up; 017 residual quality; 018 residual quality consistency; 019 residual trend breadth; 020 residual trend low-turnover; 021 downside resilience; 022 residual autocorrelation; 023 beta stability; 024 residual tail shape; 025 liquidity efficiency / lagged price impact per quote-volume; 026 residual trend efficiency; 027 weekday residual seasonality; 028 residual shock recovery; 029 residual trend efficiency follow-up; 030 BTC lead response; 031 market decoupling; 032 beta convexity; 033 beta asymmetry; 034 cross-asset lead-lag; 035 close-location pressure; 036 wick imbalance; 037 UTC block seasonality; 038 signed-volume pressure; 039 volume-price divergence; 040 residual-volatility compression; 041 average trade-size pressure; 042 funding-shock reversal; 043 trade-intensity pressure; 044 residual volatility-of-volatility stability.

## Closed / no-rescue families

Consumed unless a future proposal has a genuinely different economic mechanism and is preregistered before seeing its result: residual dispersion/trend/reversal/quality/low-volatility/tail shape/volatility-compression/volatility-of-volatility stability; funding-level carry and funding-shock reversal; volume attention/pressure/divergence; liquidity/price-impact efficiency; trade-size and transaction-intensity pressure; calendar/UTC seasonality; BTC beta stability/asymmetry/convexity/lead response; cross-asset lead-lag; OHLC close-location/wick pressure.

Forbidden rescue behavior includes sign inversion after failure, nearby-window search, cadence search, gross/leverage search, threshold search, regime cherry-picking, or combining failed signals merely to manufacture a new phase number.

## Phase044 decision

REJECTED on frozen training. Total return -14.80%, PF 0.9968, max drawdown -58.70%; 2023/2024/2025 folds were all negative with PF below 1.0. Severe return -50.66% / PF 0.9132; supersevere -79.06% / PF 0.7965. Validation remained closed and final holdout untouched. No sign/window/cadence/gross rescue is allowed.

## Phase045 admission audit — PASSED before result

Phase045 Quote-Liquidity Stability measures the 168h coefficient of variation of lagged quote volume. This is stability of dollar participation, not volume level (Phase011), signed volume (Phase038), volume-price divergence (Phase039), price impact per quote-volume (Phase025), average trade size (Phase041), or transaction-count intensity (Phase043). Frozen direction is long lower variability / short higher variability; `quote_volume.shift(1)` only; 24h rebalance, 720h BTC beta and 0.75 gross fixed before result.

## Gate preservation

Existing chronological folds, base/severe/supersevere costs and funding stress, concentration/tails, max drawdown, PF, payoff, win rate, positive days, beta/dollar neutrality, regimes and reproducibility diagnostics remain unchanged. Validation stays closed unless training passes. Final holdout stays untouched until training and validation pass and a candidate is formally frozen. V99 is excluded from V98 selection.

## Current decision

No champion exists. Phase045 is preregistered, implemented and covered by dedicated future-invariance/gross/rebalance/dollar-neutrality/holdout-access tests. Its isolated V98 workflow is the only permitted execution path. No Phase045 result has been used to alter its specification.
