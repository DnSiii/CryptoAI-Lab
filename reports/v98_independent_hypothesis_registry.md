# V98 Independent — Hypothesis Family Registry

Status: Phase055 rejected; Phase056 options feasibility failed; Phase057 on-chain feasibility failed frozen metric-access gate; Phase058 macro-risk feasibility active.

Purpose: prevent renamed repeats, rescue tuning, and pseudo-diversification. This registry is selection hygiene only; it does not inspect validation/final holdout and does not use V99 evidence.

## Executed V98 families
003-050 as previously recorded. Phase051 stopped at liquidation-data feasibility with no alpha. Phase052 no-alpha probe passed, Phase053 spot-perp candidate failed. Phase054 no-alpha COIN-M/USD-M probe passed, Phase055 candidate failed. Phase056 listed-options feasibility failed cross-fold coverage before alpha. Phase057 on-chain network-activity feasibility failed its frozen all-metrics rule before alpha.

## Closed / no-rescue families
All families through Phase050 remain closed exactly as previously recorded. Phase051 forced-liquidation partial-era/source rescue is forbidden. Phase053 spot↔USD-M basis is closed. Phase055 COIN-M↔USD-M dislocation is closed. Phase056 options IV/VRP is closed under its no-partial-era rule. Phase057 fixed on-chain activity set is closed; dropping FeeTotUSD after observing access failure is forbidden. No prior failed family may be revived by sign/window/cadence/gross/threshold/regime/symbol search or recombination.

## Phase050 decision
REJECTED without rescue tuning: training -17.41%, PF 0.9462, DD -35.18%; all 2023/2024/2025 folds negative; severe -45.80% / PF 0.8177; supersevere -72.36% / PF 0.6497 / DD -73.35%. Validation stayed closed and final holdout untouched.

## Phase051 feasibility decision
NO ALPHA EXECUTED. Binance public USD-M liquidationSnapshot feasibility was 0/30 tested training-era symbol/date combinations.

## Phase052 / Phase053
Phase052 PASS_DATA_ONLY on 30/30 spot↔USD-M checks. Phase053 frozen candidate REJECT_NO_RESCUE: base -42.6493%, DD -51.1659%, PF 0.8687; severe -63.0156%; supersevere -81.6734%; folds 2023 +5.51%, 2024 -11.22%, 2025 -38.78%.

## Phase054 / Phase055
Phase054 PASS_DATA_ONLY on 30/30 COIN-M↔USD-M checks. Phase055 REJECT_NO_RESCUE: base -46.50%, PF 0.0080, DD -46.50%, 58/1096 positive days; severe -67.05%, supersevere -84.82%; 2023/2024/2025 all negative and bull/bear/sideways all negative.

## Phase056 decision — FAIL_DATA_NO_ALPHA
ZERO ALPHA/ZERO RETURNS. 10/18 fixed option checks available. BTC/ETH EOHSummary existed on sampled 2023 dates but 0/2 sampled dates in each of 2024/2025; BTC BVOLIndex was complete. Frozen rule required all series every training year; no BVOL-only/2023-only rescue.

## Phase057 decision — FAIL_DATA_NO_ALPHA
ZERO ALPHA/ZERO RETURNS. Initial combined requests returned 403; diagnostic retry with the same frozen source/assets/metrics and a normal User-Agent isolated the issue: AdrActCnt and TxCnt were finite for BTC and ETH on every sampled 2023/2024/2025 date, while FeeTotUSD returned 403 on every check. Frozen rule required all three metrics, so Phase057 fails; dropping/substituting the inaccessible metric is forbidden.

## Phase058 preregistration — DATA FEASIBILITY ONLY
New exogenous source family: US macro/risk state via FRED public CSV. Fixed series VIXCLS, DGS10 and DFF; six fixed training-era business dates spanning 2023/2024/2025. Probe only retrieval and finite values; ZERO ALPHA/ZERO RETURNS. PASS_DATA_ONLY requires all three series on all six dates and would authorize exactly one separately preregistered Phase059 macro mechanism. No series/source substitution after observation.

## Gate preservation
Validation remains closed unless a future frozen training candidate passes. Final holdout remains untouched until training and validation pass and a candidate is formally frozen. V99 is excluded from V98 selection. No V16/V99 files/state/workflows/reports may be modified.

## Current decision
No champion exists. Phase058 is the only authorized active work and is feasibility-only. Validation and final holdout remain closed.
