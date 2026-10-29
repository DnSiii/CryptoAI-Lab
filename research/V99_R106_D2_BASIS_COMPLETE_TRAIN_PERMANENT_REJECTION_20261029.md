# V99 R106 D2 — distinct basis-convergence complete-system TRAIN: PERMANENT REJECT

Date: 2026-10-29 06:54 BRT. **D2 is permanently rejected; no retune, no promotion, no paper publication, no orders.**

## Preregistration and source
D2 was registered **before** implementation and any D2 PnL in commits [0199122](https://github.com/DnSiii/CryptoAI-Lab/commit/019912278c2007fce29b70bdedd40b8d2e8b25d9) and exact equal-quantity/gross-cap clarification [2ab0ac1](https://github.com/DnSiii/CryptoAI-Lab/commit/2ab0ac1e7f167c8761ccd1a58f757dbaf19be338). Distinct long spot / short perp positive basis-convergence hypothesis, not C1 trend or I1 options. No parameter sweep. Strict 2021-12-09..2023-10-01 TRAIN only, original 5 chronological folds and 3x2 descriptive regimes, causal t-1 basis, fixed maximum gross, fixed hold/exit, two fixed modeled friction scenarios.

Source: original archived first-party OKX 1H open receipts for BTC/ETH spot and USDT perpetual, downloaded from the already archived four-leg TRAIN artifact of [Actions 40019588739](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40019588739), reverified against original raw-page SHA256 and cursor chain by an independent source oracle. **15,864 TRAIN hours** across four instruments. No sealed validation or final holdout accessed.

## Executed CI and independent economics
Initial [Actions 40853025550](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40853025550) failed a synthetic *fixture* expectation: smooth sine basis never crosses the preregistered z>=2 threshold. Corrected **only synthetic fixture data** to include isolated threshold-crossing spikes; no strategy, threshold, folds, source, cost or gate change. Final [Actions 40853161035](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40853161035) **SUCCESS**, 5/5 synthetic adversarial tests, original-source complete D2 pre-funding TRAIN, and separately implemented independent **15,864-hour** source-to-lagged-signal-to-position-to-fee-to-NAV replay. **1,038 OPEN/EXIT events = 519 modeled position round trips**; these are hypothetical actions, not real orders or fills. The independent oracle reconciled both scenario NAVs and fold/drawdown/tail accounting, no promotion flags true.

| Preregistered metric | Severe 0.0007/side/leg | Supersevere 0.0014/side/leg |
|---|---:|---:|
| **Hypothetical TRAIN ROI, pre-funding** | **-35.0228%** | **-71.3462%** |
| Positive chronological folds | **0/5** | **0/5** |
| Maximum drawdown | **-35.0228%** | **-71.3462%** |
| Profit factor | 0.06891 | 0.03450 |
| Remove-best-hour ROI | -35.0693% | -71.3712% |
| Top 1% gain concentration | 61.8630% | 61.7187% |
| Worst 1% loss concentration | 21.5727% | 20.7433% |
| Fixed 50/50 BTC/ETH spot benchmark ROI | -54.3686% | -54.3686% |
| Failed numeric gates | **7** | **7** |

All six descriptive 3x2 regimes occurred, but neither scenario achieved positive ROI or even one positive chronological fold. The pre-funding strategy is economically poor despite being above a negative spot benchmark in the severe scenario: it **fails cash benchmark** and seven fixed gates. Supersevere also underperforms the spot benchmark. Modeled friction costs are not native historical account fees, and missing funding cash, margin/liquidation, execution/slippage and actual fills make these **NOT exchange-certified profits/losses**. These omissions cannot rescue D2 for promotion, because even pre-funding it fails decisively.

## Decision and critical path
**REJECT_D2_NUMERIC_TRAIN PERMANENTLY. NO RETUNE.** Do not change the 168h basis window, z thresholds, 168h hold, 0.25/leg cap, cost constants, strategy direction, regimes, folds, or historical partition after observing this result. Do not relabel a successful software run as a successful strategy. D2 has no right to access validation [2023-10-01,2024-01-18) or final holdout >=2024-01-18.

Next research must not serially grid-search variations of D2, C1 or I1. Distinct complete-system hypothesis requires ex-ante mechanism and hard native provenance. I1 remains SOURCE_ONLY/HOLD: 658/661 licensed original Deribit options days absent; exact historical options contract size/lot, underlying index, account fee tier, delivery charges, coin collateral, margin/liquidation and modeled fill assumptions remain unauthenticated. An authorized original nonsample day and dated license/entitlement are the first external procurement evidence; an independently authenticated equivalent provider is an alternative. Keep working on independent execution/funding provenance and complete architecture without fabricating missing market data.

**V16/V99 Frozen, paper/results, legacy champion, sealed validation and final holdout unchanged. 0/180 I1 options lifecycles economically certified. NO PROMOTION / NO ORDERS.**
