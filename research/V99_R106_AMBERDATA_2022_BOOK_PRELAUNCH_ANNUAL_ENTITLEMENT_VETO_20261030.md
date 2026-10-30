# V99 R106 — Amberdata original options-book procurement veto and exact RFQ (2026-10-30 14:xx BRT)

**SOURCE PROCUREMENT DECISION ONLY — NO DATA PURCHASE, NO ORIGINAL BOOK DELIVERY, NO ECONOMIC TRAIN, NO PROMOTION.**

## Two new first-party vendor facts that change the acquisition decision

1. Amberdata's [official online ordering FAQ](https://www.amberdata.io/online-market-data-ordering-faq) states that a **monthly subscription includes only one year of historical API lookback**; a **yearly subscription is required for full historical API access**, and S3 bulk access is an **additional purchase** available with annual subscriptions. It says not every exchange supports every dataset and asks customers to verify exchange/dataset availability in the Data Dictionary before purchase. Its standard commercial license forbids redistribution/resale/sublicensing of underlying data. A monthly subscription cannot deliver I1's 2021–2023 TRAIN in October 2026. Even annual access does not prove 2022 original books or 661-day BTC+ETH quote coverage.
2. Amberdata's [dated original 2022-01-25 announcement](https://blog.amberdata.io/amberdata-announces-crypto-options-market-support) announced Deribit options market support on **2022-01-25**, including tick-by-tick book events and one-minute snapshots. The *already frozen* I1 single-day source-feasibility target is **2022-01-23 UTC**, two days earlier. Amberdata separately advertises Deribit historical *trade* data starting **2021-05-21**, but this does not establish **prelaunch 2022-01-23 order-book events or sizes**. Prelaunch backfilled books may exist; neither assume absence nor existence. [Vendor dataset page](https://www.amberdata.io/deribit-market-data).

**Immediate decision:** do not buy monthly (insufficient lookback); do not buy annual or S3 until written evidence specifically proves original 2022-01-23 BTC and ETH options quote-event/size coverage and complete 2021-12-09..2023-09-30 TRAIN. Do not confuse trade prints or one-minute snapshots with synchronized, causally available, size-aware executable two-leg books.

## Ready-to-send vendor RFQ — NOT SENT, NOT AN ENTITLEMENT

**Recipient:** online-orders@amberdata.io (listed in official FAQ). **Subject:** Historical Deribit BTC/ETH options order-book events and full-universe availability, 2021-12 to 2023-09.

Please confirm **before any payment**, in writing:

- Whether Deribit OPTIONS **order-book-events**, not trades/OHLCV/Greeks, include **2022-01-23 00:00–24:00 UTC** for **both BTC and ETH**, notwithstanding the 2022-01-25 public options-support announcement; exact first and last book-event timestamps per asset and 2021/2022 gaps.
- A **lawfully downloadable original sample** for that exact date, including all contemporaneously listed BTC/ETH puts, strikes, expiries, best bid/ask prices and **displayed quantities**, native instrument/contract/lot units, exchange-event timestamps and independent **collector/availability timestamps**, with raw file, independently supplied SHA256, schema, capture order and complete instrument-universe manifest. Empty/no-trade contracts must not disappear from the universe silently.
- A dated full-coverage/incident manifest for **2021-12-09 through 2023-09-30** for Deribit BTC and ETH options, specifically event-level BBO/depth, quantities, daily mark and contractual delivery/index data, plus license terms for internal research and public **aggregate dashboard metrics only** (no raw-data redistribution).
- Which paid product and **written price/entitlement** includes that event history, and whether annual API plus optional S3 is necessary. The monthly one-year API lookback is insufficient; a free trial is not assumed.
- Whether vendor supplies contemporaneous **2021–2023 venue fee/lot/margin/liquidation/settlement rule evidence**, or explicitly identifies these as outside its dataset. Private account fill/fee-tier/settled-cash receipts are not implied by market data.

## Strict decision tree, unchanged I1 rules

- No written original book availability + no sample/schema/size/arrival/hash/license => **SOURCE_HOLD**. No purchase, no economic trial.
- Authorized original sample arrives => independently SHA256-check original bytes, map losslessly to existing I1 single-day feasibility contract, independently verify original clocks, fixed 28–35d expiry, 300s freshness, both strikes, lot/size and original causal signal. No change to I1 thresholds, calendar, assets or TRAIN boundary.
- Sample fails => **SOURCE_VETO_NOT_ECONOMIC_LOSS**. Passing sample is necessary but insufficient; require 661-day coverage, native fees/margin/settlement, independent self-financing replay and 5-fold 3x2 severe/supersevere gates before economic conclusion.

**Actual status:** 658/661 original quote days missing; 0/180 original option lifecycles certified. No newly acquired data, ROI, funding, fills, orders or CI economics. C1/C2/D1/G1 and other rejected architectures remain rejected, with no retuning. V16/V99 Frozen, paper/results, champion, public dashboard, sealed validation [2023-10-01,2024-01-18) and final holdout >=2024-01-18 untouched.

**Alternative:** another lawfully licensed provider (Tardis or CoinAPI) with **written original 2022-01-23 and 2021–2023 quote-event/size/clock coverage**, or a genuinely distinct preregistered architecture using source-complete native economics. Do not mislabel public trades as fills or current fee tables as historical account costs.
