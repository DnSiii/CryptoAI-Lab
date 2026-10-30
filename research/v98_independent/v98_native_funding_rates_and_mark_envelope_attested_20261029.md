# V98 Independent — Clean4 native funding and conservative mark envelope attested (2026-10-29)

**Source/cost infrastructure result, NOT a validated seven-slot trading engine or system PnL.**

## Signed funding rates — independent native source PASS
GitHub Actions `40908565200`: 100 official checksum-verified monthly fundingRate archives (Dec-2022 through Dec-2024; BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT). All **9,144 signed native funding rates** in the pinned original Clean4 artifact match the official archive **exactly (max absolute rate difference 0.0)**. 2,286 events per asset; all intervals **8h**. Official exchange `calc_time` is sometimes a few milliseconds after the 8h slot: 640 nonzero-offset events per asset, maximum **29ms**; the independent source parser preserves and reports offsets while causally mapping within a predeclared <=60s settlement-slot tolerance. No 2025/2026 or quarantined XRP accessed. No rate imputation.

## Official funding mark interval — independent SHA and coverage PASS
GitHub Actions `40907620525`: 100 checksum-verified official monthly 1h markPriceKlines ZIPs, with daily official ZIPs recovering three missing 2023-02-24 funding timestamps per asset. All **9,144** event timestamps covered; original conservative mark inside corresponding official same-hour OHLC for every event. Exact funding-tick `markPrice` is **not** attested because historical official API access returned HTTP 451/non-JSON (`40906303351`).

GitHub Actions `40908310578`: materialized **9,144-event two-sided official OHLC envelope CSV** using previous and same-hour mark candles. Source CSV SHA256 **`acbd9c6f06da70bb5bc454c539f873c1a109d1fc31dc98111e88b24387d8bbf6`**; artifact `v98-official-mark-envelope-40908310578`. All 9,144 original conservative marks inside independently verified envelopes; no synthetic fill, no future holdout.

## Signed worst-case funding settlement — executable contract PASS
GitHub Actions `40908706400`: loads original authenticated Clean4 and the pinned independent envelope artifact, validates all 9,144 event rows, and checks **4,572 vector-level signed funding cases** (2,286 event times x two funding orders), covering both long/short pay/receive signs across four assets. For a funding payer choose verified mark **upper bound**; for a receiver choose **lower bound**. In every tested case the resulting funding cashflow is <= original conservative-mark cashflow. Source and receipt are reproducible; no 2025+, no engine PnL.

**Precise remaining external evidence:** actual historical exchange funding-tick `fundingTime, fundingRate, markPrice` records for all 2,286 events per asset (or an equally authoritative tick-level export). The hourly OHLC envelope is a conservative **alternative**, not an exact native tick substitute. A new, preregistered candidate can now be stress-tested with both original conservative marks and this pinned **two-sided worst-case envelope**, plus severe/supersevere fees/slippage. No claim of exact historical account fee tier or executable slippage without account-tier and order-book evidence.

**Next critical path:** develop a genuinely new complete seven-slot high-growth V98, pass authenticated source gate, run original 30-cell physical history, independent ledger/81-corner/cross-OS and two-sided envelope sensitivity, then separate chronological validation and untouched future holdout. Only then compare frozen V98 to external benchmarks. Rejected LS/LT/LU stay rejected. No finished V98 or trading authorization.
