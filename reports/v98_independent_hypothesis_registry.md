# V98 Independent — Hypothesis Family Registry

Status: active research-control artifact after Phase050 rejection.

Purpose: prevent renamed repeats, rescue tuning, and pseudo-diversification. This registry is selection hygiene only; it does not inspect validation/final holdout and does not use V99 evidence.

## Executed V98 families

003 dispersion neutral; 004 tail-risk budget; 005 dual sleeve; 006 consensus residual; 007 residual reversal; 008 tail-budgeted dispersion; 009 funding carry neutral; 010 residual low-volatility; 011 volume attention; 012 residual skew; 013 bull dispersion; 014 non-bear dispersion; 015 continuous residual; 016 residual low-volatility follow-up; 017 residual quality; 018 residual quality consistency; 019 residual trend breadth; 020 residual trend low-turnover; 021 downside resilience; 022 residual autocorrelation; 023 beta stability; 024 residual tail shape; 025 liquidity efficiency / lagged price impact per quote-volume; 026 residual trend efficiency; 027 weekday residual seasonality; 028 residual shock recovery; 029 residual trend efficiency follow-up; 030 BTC lead response; 031 market decoupling; 032 beta convexity; 033 beta asymmetry; 034 cross-asset lead-lag; 035 close-location pressure; 036 wick imbalance; 037 UTC block seasonality; 038 signed-volume pressure; 039 volume-price divergence; 040 residual-volatility compression; 041 average trade-size pressure; 042 funding-shock reversal; 043 trade-intensity pressure; 044 residual volatility-of-volatility stability; 045 quote-liquidity stability; 046 peer-correlation crowding; 047 aggregate open-interest growth crowding; 048 aggressive taker long/short pressure; 049 top-trader-vs-broad participant-positioning divergence; 050 prior-completed-day book-depth bid/ask quoted-notional imbalance.

## Closed / no-rescue families

Consumed unless a future proposal has a genuinely different economic mechanism and is preregistered before seeing its result: residual dispersion/trend/reversal/quality/low-volatility/tail shape/volatility-compression/volatility-of-volatility stability; funding-level carry and funding-shock reversal; volume attention/pressure/divergence and quote-liquidity stability; liquidity/price-impact efficiency; trade-size and transaction-intensity pressure; calendar/UTC seasonality; BTC beta stability/asymmetry/convexity/lead response; cross-asset lead-lag; OHLC close-location/wick pressure; peer-correlation crowding; 24h aggregate open-interest growth crowding; aggressive taker long/short pressure; participant-positioning divergence; prior-completed-day book-depth bid/ask quoted-notional imbalance.

Forbidden rescue behavior includes sign inversion after failure, nearby-window search, cadence search, gross/leverage search, threshold search, regime cherry-picking, symbol-subset search, alternate participant-ratio field after Phase049 failure, alternate book-depth level/aggregation/sign after Phase050 failure, or combining failed signals merely to manufacture a new phase number.

## Phase046 decision
REJECTED despite +92.67% aggregate return: PF 1.1465 missed the frozen 1.15 gate, chronological robustness failed, severe PF 1.0673 and supersevere PF 0.9561 / DD -69.63%. No rescue or validation opening.

## Phase047 decision
REJECTED without rescue tuning: -65.34%, PF 0.7773, DD -66.59%; all chronological folds negative; severe PF 0.6273 and supersevere PF 0.4477. Validation stayed closed and final holdout untouched.

## Phase048 decision
REJECTED without rescue tuning: -64.03%, PF 0.7516, DD -66.05%; all 2023/2024/2025 folds negative; severe -83.47% / PF 0.5991 and supersevere -95.20% / PF 0.4197 / DD -95.25%. Validation stayed closed and final holdout untouched.

## Phase049 decision
REJECTED without rescue tuning. The frozen positive strictly lagged `log(sum_toptrader_long_short_ratio)-log(count_long_short_ratio)` signal produced training return -30.44%, PF 0.8949, max drawdown -35.31%, payoff 0.8979 and win rate 32.11% (586 positive days). All chronological folds were negative: 2023 -20.98% / PF 0.7858; 2024 -1.56% / PF 0.9985; 2025 -7.58% / PF 0.9300. Severe return -46.32% / PF 0.8201 / DD -49.23%; supersevere return -64.32% / PF 0.7146 / DD -65.51%. The signal lost approximately in bear, bull and sideways regimes; no regime rescue is defensible. Training data coverage was uneven (minimum symbol hourly coverage 64.17%), but the failure is broad enough that missingness is not a basis for rescue. Validation remained null and final holdout remained untouched. Participant-positioning divergence is closed, including alternate top-trader ratio substitutions.

## Phase050 decision
REJECTED without rescue tuning. The preregistered positive prior-completed-UTC-day median all-level book-depth bid/ask quoted-notional imbalance produced training return -17.41%, CAGR -3.75%, PF 0.9462, max drawdown -35.18%, payoff 0.9940 and 534 positive days. Every scored chronological fold was negative: 2023 -10.94% / PF 0.8815; 2024 -2.66% / PF 0.9846; 2025 -4.48% / PF 0.9666. Severe returned -45.80% / PF 0.8177 / DD -48.62%; supersevere returned -72.36% / PF 0.6497 / DD -73.35%. Approximate regime attribution was +2.39% in bear, -14.44% in bull and -3.73% in sideways, so a bear-only rescue is forbidden regime cherry-picking. Mean top-1 weight share was 37.12% (p95 49.79%) and mean active assets 2.98. Beta neutrality remained tight (mean absolute portfolio beta 0.0156). Training book-depth daily coverage was about 59.5%-59.8% per symbol; despite missingness, the failure is broad across folds and cost stresses and does not justify rescue. Training gate failed, validation remained closed/null, and final holdout remained untouched.

## Next frontier discipline
Phase050 is closed. No Phase051 alpha is authorized by sign inversion, alternate book-depth levels/aggregation, nearby windows, cadence, gross, threshold, regime filtering, or symbol subsets. The next candidate must introduce a genuinely new economic mechanism/data family and must be preregistered before any return is computed. A data-source feasibility/integrity probe may precede that preregistration and must not score alpha or access validation/final holdout.

## Gate preservation
Existing chronological folds, base/severe/supersevere costs and funding stress, concentration/tails, max drawdown, PF, payoff, win rate, positive days, beta/dollar neutrality, regimes and reproducibility diagnostics remain unchanged. Validation stays closed unless training passes. Final holdout stays untouched until training and validation pass and a candidate is formally frozen. V99 is excluded from V98 selection.

## Current decision
No champion exists. Phases046-050 are closed without rescue tuning. The next action is genuinely orthogonal data/mechanism discovery under a no-alpha feasibility probe; validation and final holdout remain closed.