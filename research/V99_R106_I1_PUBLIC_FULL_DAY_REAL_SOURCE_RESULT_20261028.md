# V99 I1 — real public full-day Deribit OPTIONS source: verified (2026-10-28 18:53 BRT)

**Classification: SOURCE_ONLY/HOLD — NO PROMOTION.** This is one real market-data day, not a 661-day historical options engine or economic TRAIN. No simulated/historical PnL, fills, orders, Frozen, paper, champion, sealed validation or final holdout changes.

## Pre-registered real-source execution and independent repeated fetch

Preregistered in commit `917d91df8cd0d3ccbba0eaa8229b0dee5335ad1d` **before** probe implementation. The real unauthenticated original first-of-month public Deribit OPTIONS `quotes` file for **2022-06-01** was downloaded completely and checked by the existing 661-day local importer's `scan_day` on the actual original gzip bytes (not mocks). The data remained temporary in GitHub runners; no raw vendor tape was committed or uploaded. Tardis official docs explicitly allow the first day of each month without an API key: https://docs.tardis.dev/downloadable-csv-files/api and https://docs.tardis.dev/historical-data-details/deribit.

Two **separate live CI executions**, [40775148773](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40775148773) and [40775228581](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40775228581), both SUCCESS, fetched the full original public file independently and produced **identical** original compressed-file SHA-256:

- UTC day: `2022-06-01`, HTTP **200**, complete gzip: **217,070,416 compressed bytes**.
- Complete raw CSV: **14,720,180 rows** (all rows including calls/invalid/empty quotes).
- Valid qualifying 28–45d BTC put quote rows: **1,778,798**; ETH put quote rows: **3,138,873**. These are **quote rows**, not contracts, decisions, trades, fills or profit.
- Compressed original SHA-256: `9d7b1e62fb7f16648348154ebcece472461d3038c96e61ca7e96de4ce8adcdbd` in **both independent downloads**.
- Existing importer verified gzip/CSV, arrival-day UTC, venue, causal timestamps, arrival order, and nonzero two-sided BTC+ETH put source quotes. **7/7 adversarial OFFLINE tests** passed separately; they are not source evidence.

This is an actual real-data acquisition and a real-format integration proof. It reduces uncertainty that the source importer is incompatible with a vendor day. It **does not** prove completeness of any other day, original index, option sizing, fills, native fees, margin/liquidation, delivery or profitability. It also does not constitute independent economic re-execution; the two CI jobs used the same importer but separately downloaded identical source bytes.

## Remaining critical path, explicitly external vs internal

1. **External market archive:** lawful complete **2021-12-09 through 2023-09-30** Deribit BTC+ETH `OPTIONS` BBO/size/venue+arrival quote capture, all 661 days, including entry/mark/expiry lifecycles and vendor gap provenance. **One public day is now verified; 660 days remain unverified.** Tardis standard OPTIONS plan currently advertises 4-year historical access on yearly billing and 5 years by invoice; a 2021 start requires written coverage confirmation (or independently authenticated equivalent provider). No paid license/key was acquired or exposed.
2. **External native terms:** original dated fee tier and delivery charges, contract size/minimums and amount units, collateral/margin and liquidation rules, contractual expiry index and source provenance. A backtest needs conservative size-aware **simulated** fills; actual executed fills cannot exist for untraded hypothetical historical orders.
3. **Internal economic path after source delivery:** bind all 180 fixed original intents to complete as-of option inventory, source-derived strike selection, scenario-specific conservative fills and fees, 661-day native coin wallet marks/settlements, independent economic replay, 5 chronological folds, 3x2 regimes, severe/supersevere tails/DD/benchmark gates. Preserve strict t-1 and sealed windows. Existing nonfixture cost/source gates must not be bypassed using booleans or fixtures.

**Decision:** 0/180 original historical option lifecycles economically certified; **NO TRAIN/ROI/PROMOTION/ORDERS**. Next priority is **licensed complete archive plus native dated terms**, not more synthetic alpha grids. If unavailable, source-independent engine implementation may continue but cannot be advertised as completed economic validation.
