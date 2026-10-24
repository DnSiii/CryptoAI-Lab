# V99 G1 — full TRAIN first-party source coverage and native-trade repair (2026-10-23)

**Decision: DATA_ONLY/HOLD — NO PROMOTION.** No G1 economic TRAIN has run, no ROI, no orders, no sealed validation or final holdout accessed. This document records a source blocker, not a strategy result.

## Independently reproduced first-party evidence

[Actions 40051587160](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40051587160) ran five parallel source partitions plus a separate raw-ZIP-to-hourly oracle over the **22 preregistered calendar months** (December 2021 through September 2023), **44 asset-month slots** and **42 downloaded original monthly candle ZIPs** (some month/asset slots have no eligible source to download). Original OKX monthly ZIP bytes, source listings, SHA-256 manifests, native contract IDs and derived hourly rows were archived as CI artifacts. Source collection and independent reexecution succeeded, but **the scientific coverage gate failed**:

- Fixed G1 Monday-selection/carry-to-expiry rule requires **34,958 instrument-hours** across the two assets and seven fixed expiry contracts.
- Only **528 complete 1-hour bars** were found for those exact instruments in the original monthly candle ZIPs, corresponding to **31,680 original 1-minute rows**.
- **34,430 required instrument-hours were absent** from those exact-contract candle records. This is a **source coverage failure**, not zero trades, a negative return or a strategy rejection.
- Prior [Actions 40047310996](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40047310996) independently proved that March 2022 candle ZIPs contain chronologically impossible 2025/2026 contract IDs. They MUST NOT be silently relabeled to the 2022 expiries.
- Prior [Actions 40047386032](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40047386032) proved genuine original March 2022 daily trades exist under correct 2022 contract IDs. Therefore a real alternative original source exists; absence in the monthly candle ZIP does not prove the contract never traded.

## Direct critical-path remedy, not an alpha search

Implemented `research/tools/v99_r106_g1_full_train_original_monthly.py` and `.github/workflows/v99-r106-g1-full-train-original-monthly.yml` on the requested research branch. The pipeline fixes an important first-attempt source omission: it requires **contracts carried from an earlier Monday through their actual expiry month**, not merely contracts eligible for *new* entries that month. It also independently re-executes exact source-to-hourly aggregation, retains original candle volume and prohibits any post-2023-09-30 input.

A follow-on source repair in [commit 07a4b1f](https://github.com/DnSiii/CryptoAI-Lab/commit/07a4b1f1c5fc91fb73bdc47225c04f8b4ead5596) adds **first-party original monthly trade ZIP recovery only for missing original required hours**. It verifies exact native trade IDs, prices, contract sizes, source hashes, and reconstructs missing hourly OHLC/contract volume without inventing no-trade hours. A second pass independently reconstructs from the raw trade tapes. This direct full-TRAIN run was launched as [Actions 40051665456](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40051665456); **its outcome is pending at the time of this note**. Do not claim coverage was repaired until the CI audit actually finishes and proves it.

## Follow-up actual monthly trade recovery (2026-10-23 23:04 BRT)

The corrected full source run [Actions 40052064153](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40052064153) completed **all five original-source collection jobs** with **44/44 asset-month slots collected** and no source-collection exceptions. Its five job logs jointly report **59,560,082 unique first-party trade rows** and **39,926 original-trade-derived instrument-hour bars** across the exact preregistered contract targets (these include hours not necessarily required by the fixed carry strategy and possible UTC+8 month overlap; do not equate this with complete eligible coverage). The immutable source/derived batch artifacts are approximately **1.1 GB** in aggregate. Earlier 2022 candle archives with impossible future contract labels were **not** relabeled; source was repaired with correct-ID original monthly trades, and exact duplicate trade IDs are deduplicated only if their timestamp/price/size identity matches. Conflicting IDs still fail closed.

**Critical limitation at this checkpoint:** the *separate* independent audit job was still reexecuting all original tapes and exact required carry-hour coverage. **Do not report full TRAIN source closure, PnL, economic gate success, or validation access** until that job finishes and its artifact is inspected. Historical exact-contract sizing/margin and original delivery settlement remain external source dependencies even if the independent tape audit passes.

## Additional original-venue contractual provenance risk

Official OKX documents **do not establish one unambiguous historical BTC futures contract size** for the exact 2022/2023 instruments: the 2019 launch announcement describes a BTC/USDT expiry-futures face value of **0.0001 BTC** and **08:00 UTC Friday delivery** (https://www.okx.com/en-eu/help/okx-launches-usdt-margined-futures), whereas the general expiry-futures guide currently displays **0.01 BTC** (https://www.okx.com/en-gb/help/expiry-futures; page has been updated since original publication). These are product-level documents of different vintages, **not original 2022/2023 contract-specific `ctVal` receipts**; do not infer the date or reason for the discrepancy. The current OKX fee FAQ also mentions a **0.01% expiry settlement fee** (https://www.okx.com/en-br/help/trading-fee-rules-faq), but it does not prove the historical fee schedule. A fixed `ctVal`, collateral/margin rule or settlement fee guessed from today's documents could materially distort G1 sizing, fees, liquidation and ROI. Historical contract-specific source evidence remains a **hard native-certification blocker**, even if original trade tapes fill every missing market hour.

## Still required before G1 can be judged or promoted

1. Recover original *exact-contract* hourly futures coverage for the entire fixed eligible-entry-to-expiry TRAIN, with independent per-hour receipts; if monthly trades cannot close gaps, enumerate exact missing hours and block G1 economic inference rather than filling them.
2. Obtain historically applicable native USDT-linear `ctVal`, contract lot/min size, mark/margin/liquidation and contractual delivery/settlement cash evidence for all seven expiries. Current prospective OKX instrument metadata is not a substitute for 2022/2023 terms.
3. Historical account-specific fee tiers and actual hypothetical fills cannot be certified from trade tape; run preregistered severe/supersevere cost + adverse-fill **modeled** economics and label it as modeled, not exchange-certified profits. Preserve collateral and settlement cash constraints.
4. Only if (1)-(3) support it: run one unchanged G1 TRAIN across all five fixed folds, 3x2 regimes, benchmark, tail/DD, independent source-to-cash accounting and all preregistered gates. Any gate failure permanently rejects G1. No retuning. Freeze a successful candidate before opening validation; final holdout remains sealed until formally authorized.

Frozen V16/V99, paper-results, legacy champion and dashboard promotion state were not modified. **NO PROMOTION.**
