# V98 Independent — Hypothesis Family Registry

Status: Phase062 cross-asset/system-liquidity feasibility failed without rescue. No champion.

Purpose: prevent renamed repeats, rescue tuning, and pseudo-diversification. This registry is selection hygiene only; it does not inspect validation/final holdout and does not use V99 evidence.

## Executed V98 families
003-050 as previously recorded. Phase051 stopped at liquidation-data feasibility with no alpha. Phase052 no-alpha probe passed, Phase053 spot-perp candidate failed. Phase054 no-alpha COIN-M/USD-M probe passed, Phase055 candidate failed. Phase056 listed-options feasibility failed cross-fold coverage before alpha. Phase057 on-chain network-activity feasibility failed its frozen metric-access gate before alpha. Phase058 macro-risk feasibility passed; Phase059 candidate failed. Phase060 stablecoin-liquidity feasibility passed; Phase061 candidate failed. Phase062 cross-asset/system-liquidity feasibility failed its frozen reproducibility/source-access gate before alpha.

## Closed / no-rescue families
All families through Phase050 remain closed exactly as previously recorded. Phase051 forced-liquidation partial-era/source rescue is forbidden. Phase053 spot↔USD-M basis is closed. Phase055 COIN-M↔USD-M dislocation is closed. Phase056 options IV/VRP is closed under its no-partial-era rule. Phase057 fixed on-chain activity set is closed; dropping FeeTotUSD after observing access failure is forbidden. Phase059 macro-risk is closed: no sign/window/threshold/series-subset/regime/gross/cadence rescue and no use of its 2025 failure to redesign the same family. Phase061 aggregate stablecoin liquidity is closed: no sign/window/threshold/coin-or-chain subset/source/regime/gross/cadence rescue and no use of its 2023/2025 failures or drawdown to redesign the same family. Phase062 WALCL/RRPONTSYD/WTREGEN system-liquidity family is closed under its frozen source/schema rule: no alternate provider, endpoint/source-class substitution, series dropping, date rescue, partial-series rescue or later alpha reinterpretation. No prior failed family may be revived by sign/window/cadence/gross/threshold/regime/symbol search or recombination.

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

## Phase058 decision — PASS_DATA_ONLY
FRED public CSV feasibility passed for the fixed exogenous series VIXCLS, DGS10 and DFF across the frozen training-era checks. ZERO ALPHA/ZERO RETURNS in the feasibility gate. This authorized one separately frozen Phase059 macro-risk mechanism.

## Phase059 decision — REJECT_NO_RESCUE
The frozen macro-risk training run completed its causality/invariant tests, training-only data reconstruction, candidate evaluation and isolation contract successfully. Aggregate base training was strong (+115.71%, CAGR 16.62%, PF 1.331, max DD -19.81%); severe remained +103.60% and supersevere +84.57%. However the preregistered chronological fold gate failed: 2023 +11.98% / PF 1.419; 2024 +32.97% / PF 1.492; 2025 -2.32% / PF 1.0001. Therefore validation was not opened and Phase059 is rejected without rescue.

## Phase060 decision — PASS_DATA_ONLY
DefiLlama aggregate stablecoin-liquidity feasibility passed all six fixed training-era dates using the same endpoint/schema. ZERO ALPHA/ZERO RETURNS/ZERO CRYPTO PRICE JOIN. This authorized exactly one separately frozen Phase061 mechanism.

## Phase061 decision — REJECT_NO_RESCUE
The frozen stablecoin-liquidity candidate completed 23/23 causality/invariant tests, training-only canonical reconstruction through 2025-12, candidate evaluation, isolation guard, evidence commit and artifact upload successfully. Aggregate base training was +64.89%, CAGR 10.52%, PF 1.0704, payoff 1.0077, win rate 51.51%, 940/1825 positive days, but max drawdown was -48.74%, breaching the preregistered -35% floor. Chronological folds also failed: 2023 -14.84% / PF 0.9436; 2024 +60.69% / PF 1.2163; 2025 -5.18% / PF 0.9950. Severe remained +42.66% / PF 1.0584 but DD worsened to -52.24%; supersevere +9.80% / PF 1.0372 with DD -57.63%. Therefore validation was not opened and Phase061 is rejected without rescue. The result is not eligible for sign/window/gross/regime/source/subset/cadence tuning or reinterpretation.

## Phase062 decision — FAIL_DATA_NO_ALPHA
ZERO ALPHA/ZERO RETURNS/ZERO CRYPTO PRICE JOIN. The frozen FRED public CSV source for WALCL/RRPONTSYD/WTREGEN did not complete reproducibly on the GitHub Actions runner. Runs #166, #167 and #168 all failed before producing the 18 frozen checks; #167/#168 used transport-only retries and #168 additionally bounded the identical frozen-source request to the preregistered training-era window, yet WALCL still timed out after three identical 90-second attempts. The preregistration requires all 18 checks from the frozen source/schema and explicitly forbids alternate-provider/source rescue, so this exact family is closed FAIL_DATA_NO_ALPHA. The repeated transport failure is not interpreted as economic evidence and authorizes no sign, threshold, transformation or PnL inference.

## Gate preservation
Validation remains closed unless a future frozen training candidate passes. Final holdout remains untouched until training and validation pass and a candidate is formally frozen. V99 is excluded from V98 selection. No V16/V99 files/state/workflows/reports may be modified.

## Current decision
No champion exists. Phase062 is closed FAIL_DATA_NO_ALPHA. Validation and final holdout remain closed. The next V98 hypothesis must be genuinely orthogonal to all closed families and must be preregistered before any PnL is inspected.