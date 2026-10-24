# V99 R106 — actual archived option-quote friction and historically anchored base fee (2026-10-24 BRT)

**Decision: DATA_ONLY/HOLD — NO PROMOTION.** This is **not** a strategy backtest, ROI, executable fill, full historical TRAIN, or evidence that an options strategy is profitable/unprofitable. No orders, validation, final holdout, V16/V99 Frozen, legacy champion or paper/results touched.

## Work actually executed

1. Preregistered the fixed quote-level spread metric, arrival-time checks, separate BTC/ETH and 2022/2023 strata, nearest-rank p50/p90, and independent Decimal oracle in [the ex-ante protocol](V99_R106_TARDIS_PARTIAL_QUOTE_FRICTION_PREREG_20261024.md). Subsequently preregistered a separate **illustrative standard-tier** fee sensitivity **before its CI run**, not a new strategy parameter.
2. Implemented `research_tools/v99_r106_tardis_partial_friction.py` and `research_tools/v99_r106_tardis_partial_friction_oracle.py`, wired both into the existing source-only GitHub workflow. [Actions 40083418428](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40083418428) passed the first spread/causal-timestamp oracle; [Actions 40083504198](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40083504198) passed the additional independent Decimal base-fee calculations. Archived run artifacts retain original bounded samples, hashes, entitlement status and metrics.
3. Verified the public Deribit announcement dated **2020-08-12**, effective **2020-08-24**, reducing BTC/ETH options trading fees from 0.04% to **0.03% of underlying**: https://insights.deribit.com/exchange-updates/deribit-lowers-option-trading-fees-to-make-the-market-more-accessible-to-retail-traders/ . Deribit's support page updated **2026-10-22** confirms a standard 0.03% options fee with **12.5% of option premium cap**: https://support.deribit.com/hc/en-us/articles/25944746248989-Fees . **Neither source certifies an individual account's historical 2021–2023 fee tier or guarantees that every intervening policy stayed unchanged.**

## Independently checked results — only 4,000 first-seconds-of-day quote updates

| Date | Asset | All sample rows | Positive noncrossed two-sided rows | Quoted spread p50 (bps of option mid) | Illustrative spread + two standard fees p50 (bps of option mid) | Fee-inclusive p90 (bps) |
|---|---|---:|---:|---:|---:|---:|
| 2022-01-01 | BTC | 820 | 723 | 480.00 | 711.11 | 4,235.29 |
| 2022-01-01 | ETH | 1,180 | 995 | 498.22 | 694.21 | 7,094.08 |
| 2023-01-01 | BTC | 938 | 620 | 1,500.00 | 1,850.75 | 9,166.67 |
| 2023-01-01 | ETH | 1,062 | 731 | 1,818.18 | 2,616.22 | 9,166.67 |

- **3,069/4,000** sample updates had positive noncrossed two-sided quotes; **931** had invalid/missing/nonpositive sides or sizes. No crossed/locked quotes or negative arrival lags in these bounded samples. **1,583/4,000** had local-minus-exchange timestamp greater than one second; a causally executable strategy must use actual local arrival time and reject stale books according to preregistered execution rules.
- Samples span only **15.152341 seconds** on 2022-01-01 and **30.393728 seconds** on 2023-01-01. Many listed contracts may be deep OTM and illiquid. **Do not extrapolate** these large quoted premium-relative spreads to ATM, the whole day, all contracts, five folds, or any hypothetical trading PnL.
- Spread = `20000*(ask-bid)/(ask+bid)`. Illustrative standard fee-inclusive immediate crossing = `20000*(ask-bid+min(.0003,.125*ask)+min(.0003,.125*bid))/(ask+bid)` for a BTC/ETH inverse option quoted in underlying coin. This is **not** a dollar fee, an actual fill, realized slippage, a hedged trade or a forward-looking alpha. The formula assumes standard fee and same-instant entry/exit solely to measure friction; expiry, margin, collateral, liquidity depletion and hedge costs are omitted.

## Critical-path blocker and next real step

[Actions 40083504198](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40083504198) again observed **anonymous non-sample GET Range HTTP 403** on 2022-01-02 and 2023-01-02; HEAD returned 404, which **does not establish that exchange data were absent**. The first-of-month public archive is not enough for full TRAIN. The external dependency is an **authorized, auditable L1/L2 bid/ask + sizes archive with exchange and local arrival timestamps covering 2021-12-09 through 2023-09-30, both BTC/ETH, with completeness/gap manifests**, plus historical option contract specifications, margin/settlement, account fee tier and a conservative size-aware execution model. Before any payment, confirm the provider's licensed entitlement actually includes the 2021 dates; an exchange archive or independent provider is acceptable. Native *actual hypothetical fills* cannot be certified; only reproducible fill assumptions can be validated.

**Research decision:** do **not** launch another options TRAIN candidate from these biased samples, do not re-tune rejected H1/G1/F1/C1, do not unlock [2023-10-01,2024-01-18) validation or final holdout. Until full quote access is available, concentrate subsequent research on genuinely distinct mechanisms supported by complete existing first-party data and independently verified accounting. No new superior V99 exists. **NO PROMOTION.**
