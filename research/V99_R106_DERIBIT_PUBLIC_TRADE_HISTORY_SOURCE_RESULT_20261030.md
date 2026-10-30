# V99 R106 — first-party Deribit 2022 historical options TRADE source result (2026-10-30 01:53 BRT)

**NEW ORIGINAL TRADE SOURCE VERIFIED — NOT AN OPTIONS QUOTE SOURCE; I1 STILL SOURCE HOLD; NO PROMOTION.** This is a genuine no-key Deribit historical trade API result, not another synthetic fixture or a trading backtest. Trade prints must never be substituted for contemporaneous executable two-sided quotes/depth, historical account fills, margin, native fees or option settlement marks.

## Exact reproducible execution
- Ex-ante four-request source contract committed as `86c497b2ba984070e601f6ee8c3f97e303e4292d` **before implementation and network access**: [preregistration](V99_R106_DERIBIT_HISTORY_PUBLIC_TRADE_SOURCE_PREREG_20261030.md).
- [GitHub Actions 41005209572 — SUCCESS](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41005209572), committed CI at `93c0f4d61e28062b42f5ab0174b9ed8058adbf3c`. Primary [bounded first-party fetcher](../research/tools/v99_r106_deribit_public_trade_history_probe.py) queried `history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time` for BTC/ETH option trades on the preregistered 2022-01-23 target and 2022-05-01 control; `include_old=true`, `count=100`, `sorting=asc`, one request per pair, no credentials.
- [Independent original-byte oracle](../research/verification/independent_v99_r106_deribit_public_trade_oracle.py) **PASS**: separately parsed each HTTP response, matched original SHA256, dated option names, strictly in-day timestamps, positive trade price/size, chronological order and counts; rejected false promotion flags. Original trade rows were deleted from runner before upload. Source-only metadata artifact `12955511025` (1,042-byte ZIP), no raw licensed trades distributed.

## Original first-party responses (first 100 trades, NOT complete day)

| UTC day | Currency | Original returned trades | First trade UTC | Last returned trade UTC | More pages? |
| --- | --- | ---: | --- | --- | --- |
| 2022-01-23 | BTC | 100 | 00:00:52.676 | 00:22:37.020 | yes |
| 2022-01-23 | ETH | 100 | 00:00:26.284 | 00:37:56.070 | yes |
| 2022-05-01 | BTC | 100 | 00:00:06.080 | 00:15:45.529 | yes |
| 2022-05-01 | ETH | 100 | 00:00:19.894 | 00:27:55.723 | yes |

All four original responses returned HTTP 200 with valid Deribit options trades, first attempt. The API indicated `has_more=true` on all four, so these are only **earliest 100**, not a complete 24-hour market tape or any certified 661-day coverage. In particular, **200 trades observed on 2022-01-23 across BTC/ETH does not imply 200 eligible I1 positions, 24/24 hourly BBO, or any executable 28–35-day two-strike pair.**

## Decision / actual critical path
**PUBLIC_TRADE_HISTORY_AVAILABLE_NOT_EXECUTABLE — I1 SOURCE HOLD / NO PROMOTION.** New useful fact: first-party Deribit *trade-print* history from the exact 2022-01-23 target date is available publicly without a paid quote-data credential. This offers a lower-cost independent **trade activity/instrument chronology cross-check** before buying historical options quotes. It does **not** remove any of the **658/661 missing quote/archive days**, nor certify a single I1 economic lifecycle (**0/180**).

If this public route is extended, first preregister a strictly bounded, gap-safe continuation/pagination protocol and independent original-trade-sequence checks; never treat `has_more=true` first-page rows as full-day completeness, and never reconstruct BBO/size from trades alone. The *delivery blocker* remains a lawful original BTC+ETH 661-day two-sided options quote/depth/arrival/mark/settlement archive (start with licensed 2022-01-23 sample), written usage rights, independent original digests, historical native contract/fee/margin/delivery evidence, conservative hypothetical size-aware execution, 5 chronological TRAIN folds, severe/supersevere shocks and independent accounting. A first-party historical trade stream may supplement, not replace, this archive.

No ROI/PnL was calculated. No validation [2023-10-01,2024-01-18), final holdout >=2024-01-18, Frozen V16/V99, champion, paper/results, public dashboard or order interface was opened or modified. No orders submitted.
