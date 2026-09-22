# V98 Independent Phase099 — Aggregate DEX-volume regime preregistration

Status: **PREREGISTERED / TRAINING ONLY / PARAMETERS FROZEN BEFORE PNL**.

Phase098 passed DATA_ONLY feasibility with 1,096/1,096 training-era days, zero duplicates/invalid values and full 2023-01-01..2025-12-31 coverage from the frozen DefiLlama aggregate DEX totalDataChart. Phase099 is the single authorized alpha test for this information class.

## Frozen causal signal

At UTC day t, use DEX volume observations strictly before t. Compute the sum of aggregate DEX volume over the latest 7 completed calendar days and compare it with the immediately preceding non-overlapping 7 completed calendar days. If recent-7d sum > prior-7d sum, hold the fixed five-asset basket LONG for day t. If recent-7d sum < prior-7d sum, hold the basket SHORT. Exact tie or unavailable inputs => cash. This 7-vs-7 construction is frozen to reduce day-of-week seasonality without threshold fitting.

## Frozen exposure/execution

Basket: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT. Active gross 0.75 equally weighted (0.15 absolute per symbol). Rebalance once daily at 00:00 UTC after the completed-volume windows are known. No threshold, z-score, alternate lookback, volume-price interaction, volatility targeting, regime filter, symbol/chain selection, stop, take-profit, leverage scaling, alternate source, rescue or parameter sweep.

Funding uses canonical point-in-time data. Turnover costs use existing V98 BASE/severe/supersevere conventions on every weight change; no relaxation after results.

## Mandatory training gates

Training only through 2025-12-31 with chronological 2023/2024/2025 folds; validation closed; 2026 and final holdout untouched. PASS_TRAINING requires aggregate net return >0; daily PF >1.10; max DD >=-35%; every chronological fold return >0; severe return >0 and PF >1.0; supersevere return >0 and PF >1.0; no single asset >60% absolute contribution; top-10 absolute daily-return share <=60%; standard regime/concentration/tail diagnostics and reproducibility hashes.

Any failed mandatory gate => **REJECT_NO_RESCUE**. PASS_TRAINING only authorizes separately frozen validation. No V99/V16 evidence, no Phase083 selection use, no 2026 tuning, and no direction/window/threshold/basket/gross/cadence/regime/source/cost rescue.