# V98 Independent — Hypothesis Family Registry

Status: research-control artifact created after Phase040 rejection, before selecting Phase041.

Purpose: prevent renamed repeats, rescue tuning, and pseudo-diversification. This registry is selection hygiene only; it does not inspect validation/final holdout and does not use V99 evidence.

## Executed V98 families

- 003 dispersion neutral
- 004 tail-risk budget
- 005 dual sleeve
- 006 consensus residual
- 007 residual reversal
- 008 tail-budgeted dispersion
- 009 funding carry neutral
- 010 residual low-volatility
- 011 volume attention
- 012 residual skew
- 013 bull dispersion
- 014 non-bear dispersion
- 015 continuous residual
- 016 residual low-volatility follow-up
- 017 residual quality
- 018 residual quality consistency
- 019 residual trend breadth
- 020 residual trend low-turnover
- 021 downside resilience
- 022 residual autocorrelation
- 023 beta stability
- 024 residual tail shape
- 025 liquidity efficiency / lagged price impact per quote-volume
- 026 residual trend efficiency
- 027 weekday residual seasonality
- 028 residual shock recovery
- 029 residual trend efficiency follow-up
- 030 BTC lead response
- 031 market decoupling
- 032 beta convexity
- 033 beta asymmetry
- 034 cross-asset lead-lag
- 035 close-location pressure
- 036 wick imbalance
- 037 UTC block seasonality
- 038 signed-volume pressure
- 039 volume-price divergence
- 040 residual-volatility compression

## Closed / no-rescue families

The following families are considered consumed unless a future proposal has a genuinely different economic mechanism and is preregistered before seeing its result: residual dispersion/trend/reversal/quality/low-volatility/tail shape; funding-level carry; volume attention/pressure/divergence; liquidity/price-impact efficiency; calendar/UTC seasonality; BTC beta stability/asymmetry/convexity/lead response; cross-asset lead-lag; OHLC close-location/wick pressure; residual-volatility compression.

Forbidden rescue behavior includes sign inversion after failure, nearby-window search, cadence search, gross/leverage search, threshold search, regime cherry-picking, or combining failed signals merely to manufacture a new phase number.

## Phase041 admission rule

Before Phase041 implementation, require all of the following:
1. Economic mechanism is materially distinct from the closed families above.
2. Inputs are available point-in-time and can be lagged deterministically.
3. Direction, windows, cadence, gross and neutralization are frozen in a preregistration before any Phase041 result.
4. Existing chronological folds, base/severe/supersevere costs and funding stress, concentration/tails, max drawdown, PF, payoff, win rate, positive days, beta/dollar neutrality, regimes and reproducibility diagnostics remain unchanged.
5. Validation remains closed unless training gate passes; final holdout remains untouched until a candidate passes training and validation and is formally frozen.
6. No V99 result, workflow, report or paper state may be used for V98 selection.

## Current decision

Phase040 is rejected. No champion exists. Phase041 is intentionally not assigned until a mechanism passes the overlap audit above; this is an anti-overfit decision, not a pause in research.
