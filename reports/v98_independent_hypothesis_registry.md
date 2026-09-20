# V98 Independent — Hypothesis Family Registry

Status: Phase052 feasibility passed; Phase053 preregistered before training result.

Purpose: prevent renamed repeats, rescue tuning, and pseudo-diversification. This registry is selection hygiene only; it does not inspect validation/final holdout and does not use V99 evidence.

## Executed V98 families
003-050 as previously recorded. Phase051 stopped at liquidation-data feasibility with no alpha. Phase052 was a no-alpha feasibility probe only.

## Closed / no-rescue families
All families through Phase050 remain closed exactly as previously recorded. Phase051 forced-liquidation source substitution/partial-era rescue is forbidden. No prior failed family may be revived by sign/window/cadence/gross/threshold/regime/symbol search or recombination.

## Phase046-050 decisions
Preserved in their committed reports/history. Phase050: REJECTED without rescue tuning: training -17.41%, PF 0.9462, DD -35.18%; all 2023/2024/2025 folds negative; severe -45.80% / PF 0.8177; supersevere -72.36% / PF 0.6497 / DD -73.35%. Validation stayed closed and final holdout untouched.

## Phase051 feasibility decision
NO ALPHA EXECUTED. Binance public USD-M liquidationSnapshot feasibility was 0/30 tested training-era symbol/date combinations, so the source is infeasible under the reproducibility protocol. No partial-era or alternate-source rescue.

## Phase052 feasibility decision
PASSED DATA FEASIBILITY ONLY; NO ALPHA EXECUTED. Binance public spot and USD-M perpetual 1h archives were matched successfully on 30/30 checks spanning BTC/ETH/BNB/XRP/SOL and six dates across 2023/2024/2025. The probe explicitly computed no basis, alpha, ranks, thresholds, or returns and accessed neither validation nor final holdout. This authorizes preregistration of one independent spot-perpetual basis mechanism, not parameter search.

## Phase053 preregistration — frozen before result
Economic mechanism: cross-sectional convergence of spot-vs-USD-M perpetual basis. Universe is fixed to BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT. Training is fixed to 2023-01-01 through 2025-12-31. At hour t, score is the NEGATIVE of the trailing 24h mean log(perpetual_close/spot_close), using basis observations only through t-1. Scores are cross-sectionally ranked/demeaned, L1 normalized to gross 0.75, and positions rebalance every 8h. Direction is fixed ex ante as convergence: relatively rich perpetuals short, relatively cheap perpetuals long. No sign inversion is allowed after result.

Execution assumptions are frozen: base fee+slippage 7 bps/side, severe 12 bps/side, supersevere 20 bps/side, plus actual Binance funding where public monthly funding archives are available. Evaluation must report chronological 2023/2024/2025 folds, base/severe/supersevere, max drawdown, daily Profit Factor, payoff, win rate, positive days, bull/bear/sideways attribution, concentration/active assets/turnover and data coverage. Training gate is fixed before result: base return >0 and daily PF >=1.15; severe return >0; supersevere daily PF >=1.0; at least 2/3 yearly folds positive. Failure means REJECT_NO_RESCUE: no alternate sign, lookback, rebalance, gross, costs, threshold, regime, or symbol subset.

## Gate preservation
Validation remains closed unless the frozen Phase053 training gate passes. Final holdout remains untouched until training and validation pass and a candidate is formally frozen. V99 is excluded from V98 selection. No V16/V99 files/state/workflows/reports may be modified.

## Current decision
No champion exists. Phase053 is the only authorized active alpha and is frozen before its training result. Validation and final holdout remain closed.