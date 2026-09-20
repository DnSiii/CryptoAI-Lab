# V98 Independent — Hypothesis Family Registry

Status: Phase055 rejected; Phase056 options feasibility failed cross-fold coverage with zero alpha; Phase057 on-chain feasibility preregistered.

Purpose: prevent renamed repeats, rescue tuning, and pseudo-diversification. This registry is selection hygiene only; it does not inspect validation/final holdout and does not use V99 evidence.

## Executed V98 families
003-050 as previously recorded. Phase051 stopped at liquidation-data feasibility with no alpha. Phase052 was a no-alpha feasibility probe. Phase053 executed one frozen spot-perpetual basis-convergence alpha and failed. Phase054 was a no-alpha COIN-M/USD-M feasibility probe and passed 30/30 paired checks. Phase055 executed the sole frozen COIN-M/USD-M collateral-dislocation convergence candidate and failed training. Phase056 tested listed-options historical-data feasibility only and failed the cross-fold coverage rule before alpha.

## Closed / no-rescue families
All families through Phase050 remain closed exactly as previously recorded. Phase051 forced-liquidation source substitution/partial-era rescue is forbidden. Phase053 spot↔USD-M perpetual basis/convergence is closed. Phase055 COIN-M↔USD-M collateral-dislocation convergence is closed. Phase056 options implied-volatility/volatility-risk-premium family is closed under its frozen no-partial-era-rescue rule. No prior failed family may be revived by sign/window/cadence/gross/threshold/regime/symbol search or recombination.

## Phase050 decision
REJECTED without rescue tuning: training -17.41%, PF 0.9462, DD -35.18%; all 2023/2024/2025 folds negative; severe -45.80% / PF 0.8177; supersevere -72.36% / PF 0.6497 / DD -73.35%. Validation stayed closed and final holdout untouched.

## Phase051 feasibility decision
NO ALPHA EXECUTED. Binance public USD-M liquidationSnapshot feasibility was 0/30 tested training-era symbol/date combinations. No partial-era or alternate-source rescue.

## Phase052 feasibility decision
PASSED DATA FEASIBILITY ONLY; NO ALPHA EXECUTED. Binance public spot and USD-M perpetual 1h archives matched on 30/30 training-era checks. This authorized exactly one independent spot-perpetual basis mechanism.

## Phase053 decision — REJECT_NO_RESCUE
Frozen candidate failed training. Base -42.6493%, DD -51.1659%, daily PF 0.8687; severe -63.0156%, PF 0.7702; supersevere -81.6734%, PF 0.6379. Folds: 2023 +5.51%, 2024 -11.22%, 2025 -38.78%. Validation remained closed and final holdout untouched. No rescue is authorized.

## Phase054 feasibility decision — PASS_DATA_ONLY
PASSED DATA FEASIBILITY ONLY; ZERO ALPHA/ZERO RETURNS. Public Binance COIN-M and USD-M 1h archives were paired on 30/30 fixed training-era asset/date checks across BTC, ETH, BNB, XRP and SOL in 2023/2024/2025. This authorized exactly one separately preregistered collateral-segment dislocation mechanism.

## Phase055 decision — REJECT_NO_RESCUE
Frozen COIN-M↔USD-M convergence candidate failed training decisively. Base return -46.50%, daily PF 0.0080, max drawdown -46.50%, 58/1096 positive days; severe -67.05%, supersevere -84.82%. Chronological folds all failed: 2023 -17.68%, 2024 -18.23%, 2025 -20.52%. Bull/bear/sideways regimes were all negative. Both-leg turnover was 968.5 and the best day was only +0.025%. Validation remained closed; final holdout untouched. No rescue is authorized.

## Phase056 decision — FAIL_DATA_NO_ALPHA
ZERO ALPHA/ZERO RETURNS. 10/18 fixed training-era option-archive checks were available. BTC and ETH EOHSummary were present on both sampled 2023 dates (26-column chain with IV/Greeks/OI) but 0/2 sampled dates in each of 2024 and 2025; BTC BVOLIndex was 2/2 in each year. The frozen rule required all three series in every training year, so feasibility failed. No BVOL-only or 2023-only rescue is authorized. Validation/final holdout stayed untouched.

## Phase057 preregistration — DATA FEASIBILITY ONLY
New orthogonal source family: public on-chain network activity via Coin Metrics Community API. Fixed BTC/ETH metrics are AdrActCnt, TxCnt and FeeTotUSD at 1d frequency, sampled on two frozen dates in each of 2023/2024/2025. Probe only presence/timestamps/finite values; ZERO ALPHA/ZERO RETURNS. If every metric is available for both assets in every sampled training year, exactly one Phase058 on-chain economic mechanism may be separately preregistered before PnL. No partial-era/source-substitution rescue.

## Gate preservation
Validation remains closed unless a future frozen training candidate passes. Final holdout remains untouched until training and validation pass and a candidate is formally frozen. V99 is excluded from V98 selection. No V16/V99 files/state/workflows/reports may be modified.

## Current decision
No champion exists. Phase057 is the only authorized active work and is feasibility-only. Validation and final holdout remain closed.
