# V99 — H1 independent zero-friction TRAIN falsification (2026-10-24 BRT)

**H1 remains PERMANENTLY REJECTED. NO RETUNE. NO PROMOTION.** This is a read-only economic falsification of the already rejected fixed strategy, **not** a new candidate or a new performance claim. It narrows the actual critical path by proving that account fee-tier retrieval cannot rescue H1.

## Executed evidence, not a synthetic-only test

- [Actions 40075732269](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40075732269): **SUCCESS**, using the original 15,864 hourly OKX spot TRAIN opens ([source run 40019588739](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40019588739)), original 188 Deribit DVOL weekly observations ([source run 40072202459](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40072202459)) and unchanged four-scenario original H1 journal ([economic run 40072415531](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40072415531)).
- Re-ran the **existing independent original-source-to-fees-to-cash oracle** before computing any counterfactual. Original H1 was already preregistered, independently accounted and rejected; no strategy parameter, signal, decision, fold or original record was modified.
- A **new separate independent implementation** calculated fixed H1 decisions with *exactly zero fees and zero slippage*. Two different cashflow identities — (a) hourly cash + asset quantities and (b) weekly target-weighted original price ratios — agreed at **all 15,864 TRAIN hours**. Full original-source receipt hashes, strict hour grid and 94 fixed Monday decisions were checked. Result archived in artifact **12553445978**.

## Read-only economic result

| Metric | No fees / no slippage (unrealistically favorable) | Severe modeled | Supersevere modeled |
|---|---:|---:|---:|
| Full TRAIN compounded ROI | **-26.6400%** | **-27.9089%** | **-29.1556%** |
| Positive chronological folds | **1/5** | **1/5** | **1/5** |
| Maximum drawdown | **-42.9586%** | **-43.3076%** | **-43.6545%** |

Removing **all** trading friction improved modeled compounded ROI by only **1.2688 percentage points** versus severe and **2.5156 percentage points** versus supersevere. Even under the impossible zero-friction assumption, H1 loses 26.64%, has 1/5 positive folds (required severe >=4/5) and breaches the -35% drawdown limit. **H1 has no demonstrated gross economic edge; the loss is not caused primarily by the unknown historical account fee tier.** No account profit, realized paper or live fill is claimed.

## Actual next critical path and external evidence

1. **Do not repeat H1, C1/C2/D1/E1/F1/G1 or serial directional spot reweighting.** Fee-tier collection remains a deployment/provenance obligation for *future* tradable candidates, but is no longer an H1 rescue task.
2. A distinct options-volatility-risk-premium engine requires *point-in-time executable historical option bid/ask and size/depth* at the planned entry/exit decisions, plus historical contract specifications, fee schedule, margin, expiry and settlement data. Historical Deribit **trade prints/IV and DVOL alone are not executable quotes**. Deribit's [official institutional guide, historical-data section](https://statics.deribit.com/files/DeribitInstitutionalSetupGuide.pdf) lists historical instruments and trade endpoints; it does not itself establish an as-of order-book replay. **Do not infer historical quotes from current book endpoints.**
3. Concrete alternatives: obtain licensed archived Deribit L1/L2 snapshots with original timestamps and provenance from a market-data provider, or request archival book data from the exchange; then preregister **one** economically justified options system with a fixed execution/cost envelope before reading TRAIN returns. If executable historical quotes are unavailable, reject that path *before* any strategy optimization and evaluate a different mechanism with genuine tradeable native receipts.
4. For any future OKX spot/perpetual candidate, exact account-applicable **2021–2023 fee-tier records** and account trade/fill reports (or independently justified conservative marketable-fill envelope) remain unproven. Perpetuals additionally require settled funding, historical margin/lot terms and liquidation modeling. None may be called exchange-certified without actual provenance.

**Sealed boundaries:** TRAIN ends before 2023-10-01. Validation [2023-10-01,2024-01-18) and final holdout >=2024-01-18 were not accessed. V16 Frozen, V99 Frozen, legacy champion, paper/results, dashboard claims and order systems were not modified. This CI success means *the H1 rejection is independently robust*, **not** a validated superior engine.
