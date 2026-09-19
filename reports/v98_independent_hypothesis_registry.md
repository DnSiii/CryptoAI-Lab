# V98 Independent — Hypothesis Family Registry

Status: active research-control artifact after Phase047 rejection.

Purpose: prevent renamed repeats, rescue tuning, and pseudo-diversification. This registry is selection hygiene only; it does not inspect validation/final holdout and does not use V99 evidence.

## Executed V98 families

003 dispersion neutral; 004 tail-risk budget; 005 dual sleeve; 006 consensus residual; 007 residual reversal; 008 tail-budgeted dispersion; 009 funding carry neutral; 010 residual low-volatility; 011 volume attention; 012 residual skew; 013 bull dispersion; 014 non-bear dispersion; 015 continuous residual; 016 residual low-volatility follow-up; 017 residual quality; 018 residual quality consistency; 019 residual trend breadth; 020 residual trend low-turnover; 021 downside resilience; 022 residual autocorrelation; 023 beta stability; 024 residual tail shape; 025 liquidity efficiency / lagged price impact per quote-volume; 026 residual trend efficiency; 027 weekday residual seasonality; 028 residual shock recovery; 029 residual trend efficiency follow-up; 030 BTC lead response; 031 market decoupling; 032 beta convexity; 033 beta asymmetry; 034 cross-asset lead-lag; 035 close-location pressure; 036 wick imbalance; 037 UTC block seasonality; 038 signed-volume pressure; 039 volume-price divergence; 040 residual-volatility compression; 041 average trade-size pressure; 042 funding-shock reversal; 043 trade-intensity pressure; 044 residual volatility-of-volatility stability; 045 quote-liquidity stability; 046 peer-correlation crowding; 047 aggregate open-interest growth crowding.

## Closed / no-rescue families

Consumed unless a future proposal has a genuinely different economic mechanism and is preregistered before seeing its result: residual dispersion/trend/reversal/quality/low-volatility/tail shape/volatility-compression/volatility-of-volatility stability; funding-level carry and funding-shock reversal; volume attention/pressure/divergence and quote-liquidity stability; liquidity/price-impact efficiency; trade-size and transaction-intensity pressure; calendar/UTC seasonality; BTC beta stability/asymmetry/convexity/lead response; cross-asset lead-lag; OHLC close-location/wick pressure; peer-correlation crowding; 24h aggregate open-interest growth crowding.

Forbidden rescue behavior includes sign inversion after failure, nearby-window search, cadence search, gross/leverage search, threshold search, regime cherry-picking, symbol-subset search, or combining failed signals merely to manufacture a new phase number.

## Phase044 decision

REJECTED: total return -14.80%, PF 0.9968, max drawdown -58.70%; all 2023/2024/2025 folds negative; severe PF 0.9132 and supersevere PF 0.7965. Validation remained closed.

## Phase045 decision

REJECTED: total return -55.16%, PF 0.8985, max drawdown -68.55%, worst day -23.61%. Only 2023 was positive (+8.66%, PF 1.1068); 2024 and 2025 were negative. Severe PF 0.8304; supersevere PF 0.7345. Validation remained closed.

## Phase046 decision

REJECTED despite being materially stronger in aggregate: total return +92.67%, PF 1.1465, max drawdown -32.79%, payoff 1.2258. It misses the frozen PF>=1.15 training gate and lacks chronological robustness: 2023 -20.68% / PF 0.7532, 2024 +0.71% / PF 1.0123, 2025 -6.04% / PF 0.9491. Severe PF 1.0673 is below 1.10; supersevere return -40.98% / PF 0.9561 / DD -69.63%. No near-threshold rescue or validation opening is allowed.

## Phase047 decision

REJECTED without rescue tuning. The external OI source passed the repaired acquisition/integrity gate on all 80 sampled symbol-days after deterministic timestamp sorting and causal hourly canonicalization. The frozen negative 24h OI-growth signal then produced training return -65.34%, PF 0.7773, max drawdown -66.59%, payoff 0.9362 and win rate 36.99%. All chronological folds were negative: 2023 -18.13% / PF 0.8153; 2024 -2.97% / PF 0.9825; 2025 -37.28% / PF 0.5872. Severe PF 0.6273 and supersevere PF 0.4477 with -96.41% max drawdown. Validation stayed closed and final holdout stayed untouched. The 24h OI-growth crowding family is closed; no sign inversion, alternate OI window, smoothing, cadence, gross, threshold, regime or subset rescue is permitted.

## Phase048 preregistered frontier

Phase048 moves to a different derivatives mechanism available in the already-audited public metrics schema: taker-side buy/sell pressure (`sum_taker_long_short_vol_ratio`). This is not candle volume attention or signed price-volume interaction: it measures aggressor-side futures order flow directly. The frozen proposal uses the strictly lagged latest hourly log taker ratio, cross-sectional negative percentile rank (contrarian to aggressive-side crowding), daily rebalance, 720h BTC-beta plus dollar neutralization, BTC excluded from alpha holdings and gross target/cap 0.75. No threshold, smoothing/window search, regime filter or combination with Phase047 is allowed. A dedicated preregistration must exist before any Phase048 return is computed.

## Gate preservation

Existing chronological folds, base/severe/supersevere costs and funding stress, concentration/tails, max drawdown, PF, payoff, win rate, positive days, beta/dollar neutrality, regimes and reproducibility diagnostics remain unchanged. Validation stays closed unless training passes. Final holdout stays untouched until training and validation pass and a candidate is formally frozen. V99 is excluded from V98 selection.

## Current decision

No champion exists. Phases044-047 are closed without rescue tuning. Phase048 is the next orthogonal preregistered frontier; validation and final holdout remain closed.
