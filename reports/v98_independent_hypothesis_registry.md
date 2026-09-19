# V98 Independent — Hypothesis Family Registry

Status: active research-control artifact after Phase048 rejection.

Purpose: prevent renamed repeats, rescue tuning, and pseudo-diversification. This registry is selection hygiene only; it does not inspect validation/final holdout and does not use V99 evidence.

## Executed V98 families

003 dispersion neutral; 004 tail-risk budget; 005 dual sleeve; 006 consensus residual; 007 residual reversal; 008 tail-budgeted dispersion; 009 funding carry neutral; 010 residual low-volatility; 011 volume attention; 012 residual skew; 013 bull dispersion; 014 non-bear dispersion; 015 continuous residual; 016 residual low-volatility follow-up; 017 residual quality; 018 residual quality consistency; 019 residual trend breadth; 020 residual trend low-turnover; 021 downside resilience; 022 residual autocorrelation; 023 beta stability; 024 residual tail shape; 025 liquidity efficiency / lagged price impact per quote-volume; 026 residual trend efficiency; 027 weekday residual seasonality; 028 residual shock recovery; 029 residual trend efficiency follow-up; 030 BTC lead response; 031 market decoupling; 032 beta convexity; 033 beta asymmetry; 034 cross-asset lead-lag; 035 close-location pressure; 036 wick imbalance; 037 UTC block seasonality; 038 signed-volume pressure; 039 volume-price divergence; 040 residual-volatility compression; 041 average trade-size pressure; 042 funding-shock reversal; 043 trade-intensity pressure; 044 residual volatility-of-volatility stability; 045 quote-liquidity stability; 046 peer-correlation crowding; 047 aggregate open-interest growth crowding; 048 aggressive taker long/short pressure.

## Closed / no-rescue families

Consumed unless a future proposal has a genuinely different economic mechanism and is preregistered before seeing its result: residual dispersion/trend/reversal/quality/low-volatility/tail shape/volatility-compression/volatility-of-volatility stability; funding-level carry and funding-shock reversal; volume attention/pressure/divergence and quote-liquidity stability; liquidity/price-impact efficiency; trade-size and transaction-intensity pressure; calendar/UTC seasonality; BTC beta stability/asymmetry/convexity/lead response; cross-asset lead-lag; OHLC close-location/wick pressure; peer-correlation crowding; 24h aggregate open-interest growth crowding; aggressive taker long/short pressure.

Forbidden rescue behavior includes sign inversion after failure, nearby-window search, cadence search, gross/leverage search, threshold search, regime cherry-picking, symbol-subset search, or combining failed signals merely to manufacture a new phase number.

## Phase046 decision

REJECTED despite being materially stronger in aggregate: total return +92.67%, PF 1.1465, max drawdown -32.79%, payoff 1.2258. It misses the frozen PF>=1.15 training gate and lacks chronological robustness: 2023 -20.68% / PF 0.7532, 2024 +0.71% / PF 1.0123, 2025 -6.04% / PF 0.9491. Severe PF 1.0673 is below 1.10; supersevere return -40.98% / PF 0.9561 / DD -69.63%. No near-threshold rescue or validation opening is allowed.

## Phase047 decision

REJECTED without rescue tuning. The external OI source passed the repaired acquisition/integrity gate on all 80 sampled symbol-days after deterministic timestamp sorting and causal hourly canonicalization. The frozen negative 24h OI-growth signal produced training return -65.34%, PF 0.7773, max drawdown -66.59%, payoff 0.9362 and win rate 36.99%. All chronological folds were negative. Severe PF 0.6273 and supersevere PF 0.4477. Validation stayed closed and final holdout stayed untouched.

## Phase048 decision

REJECTED without rescue tuning. Frozen strictly lagged negative taker-ratio pressure produced training return -64.03%, PF 0.7516, max drawdown -66.05%, payoff 0.8783 and win rate 34.47% (629 positive days). All chronological folds were negative: 2023 -20.67% / PF 0.7566; 2024 -32.03% / PF 0.6944; 2025 -13.69% / PF 0.8576. Severe return -83.47% / PF 0.5991 and supersevere return -95.20% / PF 0.4197 / DD -95.25%. Validation stayed closed and final holdout stayed untouched. Aggressive taker-pressure is closed; no sign/window/cadence/gross/threshold/regime/subset rescue is permitted.

## Phase049 preregistered frontier

Phase049 moves to participant-positioning divergence using two already-audited public metrics: `sum_toptrader_long_short_ratio` versus `count_long_short_ratio`. This is not taker flow or OI growth: it asks whether top-trader positioning is relatively more bullish/bearish than broad-account positioning. The frozen signal is `log(sum_toptrader_long_short_ratio) - log(count_long_short_ratio)`, strictly lagged one observation, with positive cross-sectional direction (follow relative top-trader positioning), daily rebalance, 720h BTC-beta plus dollar neutralization, BTC excluded from alpha holdings and gross target/cap 0.75. No alternate top-trader field, sign inversion, threshold, smoothing/window search, regime filter, cadence/gross search, subset selection, or combination with prior phases is allowed. Dedicated Phase049 preregistration was committed before implementation/result computation.

## Gate preservation

Existing chronological folds, base/severe/supersevere costs and funding stress, concentration/tails, max drawdown, PF, payoff, win rate, positive days, beta/dollar neutrality, regimes and reproducibility diagnostics remain unchanged. Validation stays closed unless training passes. Final holdout stays untouched until training and validation pass and a candidate is formally frozen. V99 is excluded from V98 selection.

## Current decision

No champion exists. Phases046-048 are closed without rescue tuning. Phase049 is the next orthogonal preregistered frontier; validation and final holdout remain closed.
