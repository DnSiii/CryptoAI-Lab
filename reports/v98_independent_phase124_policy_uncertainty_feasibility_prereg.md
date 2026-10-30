# V98 Independent — Phase124 US Policy Uncertainty DATA_ONLY Preregistration

Status: FROZEN BEFORE ANY OBSERVATION VALUE, CRYPTO RETURN, CORRELATION, ALPHA OR PNL.

## Scientific purpose
Test a new exogenous information-risk family: US economic-policy uncertainty. This is distinct from crypto market/derivatives/on-chain families, Fed balance-sheet liquidity, DXY, VIX/rates macro-risk, stablecoins, CFTC positioning and HY credit stress. Phase124 is data/integrity feasibility only.

## Frozen source and series
Source: FRED public CSV. Series fixed ex ante: `USEPUINDXD` (Economic Policy Uncertainty Index for United States, daily). Training window fixed at 2023-01-01 through 2025-12-31 inclusive. No provider substitution, series substitution, alternate EPU construction, threshold, sign, lag, smoothing, lookback, subset rescue or imputation after inspection.

## Frozen integrity gate
Canonicalize ISO `observation_date`, retain only finite `USEPUINDXD` observations inside the training window, and compute deterministic payload/canonical SHA-256 hashes. PASS_DATA_ONLY requires HTTP 200; at least 95% coverage of frozen calendar days; zero malformed dates; zero post-canonical duplicate finite dates; and zero finite rows outside training. Missing source-calendar values are counted and never filled/interpolated. The report must not emit observation values or descriptives.

## Isolation / anti-leakage contract
Training only. Validation and final holdout remain unopened. V16 and V99 evidence/state/workflows/reports are forbidden inputs. Phase124 must not compute crypto returns, correlations, alpha, PnL, parameter search, regimes, or direction.

## Decision
Failure => `REJECT_DATA_SOURCE_NO_RESCUE` and close this exact family. PASS => only authorizes a separately preregistered Phase125 economic mechanism before any crypto PnL; Phase125 must freeze causality/lag/exposure/gates and preserve chronological folds, realistic costs/funding, severe/supersevere stress, regimes, tails/concentration, DD, PF, payoff, win rate, positive days and reproducibility.
