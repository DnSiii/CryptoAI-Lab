# V98 Independent — Phase062 Cross-Asset Liquidity Feasibility Preregistration

Status: PREREGISTERED BEFORE ANY ALPHA OR PNL.

## Scientific purpose
Test whether a genuinely external, orthogonal cross-asset liquidity family is reproducibly obtainable over the V98 training era before defining any trading rule. This phase is DATA FEASIBILITY ONLY. It must not calculate crypto returns, join crypto prices, select a sign, threshold, lookback, regime, exposure, or inspect validation/final holdout.

## Frozen source and variables
Source: FRED public CSV, same reproducible transport class already proven usable by V98 but with a distinct economic family from Phase058 macro-risk.

Fixed series:
- WALCL — Federal Reserve total assets (system liquidity / balance-sheet scale)
- RRPONTSYD — Overnight Reverse Repurchase Agreements: Treasury Securities Sold by the Federal Reserve in the Temporary Open Market Operations
- WTREGEN — U.S. Treasury General Account balance at Federal Reserve Banks

No substitution, alternate provider, series dropping, transformation search, sign choice, threshold, or subset rescue after observation.

## Frozen training-era checks
Require finite observations available on or before each fixed UTC date for all three series:
- 2023-03-15
- 2023-09-15
- 2024-03-15
- 2024-09-16
- 2025-03-17
- 2025-09-15

For lower-frequency series, the feasibility check must use only the most recent observation whose publication/observation date is not after the fixed date. No forward fill from future observations and no interpolation.

## Decision rule
PASS_DATA_ONLY only if all 18 series/date checks return finite numeric values from the frozen source/schema and causality can be represented without future observations. Otherwise FAIL_DATA_NO_ALPHA and close this exact family without source/date/series-subset rescue.

## If PASS_DATA_ONLY
Exactly one subsequent Phase063 mechanism may be preregistered BEFORE any crypto PnL is computed. Phase063 must freeze its economic transformation, lag, cadence, exposure and gate before PnL; use training-only crypto data; realistic trading costs and funding; base/severe/supersevere stress; chronological 2023/2024/2025 folds; regimes; concentration/tails; max drawdown; Profit Factor; payoff; win rate; positive days; reproducibility and anti-overfit checks. Validation remains closed until all frozen training gates pass. Final holdout remains untouched until training and validation pass and a candidate is formally frozen.

## Isolation contract
Engine namespace: V98 Independent only. V99 evidence/state/workflows/reports and V16 Frozen are forbidden inputs. Phase059 and Phase061 failures must not be used to choose signs, windows, thresholds, gross, regimes or rescue variants for this family.
