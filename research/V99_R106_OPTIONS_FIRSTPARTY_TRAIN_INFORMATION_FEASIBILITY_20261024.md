# V99 — first-party options-information source feasibility (2026-10-24 BRT)

**DATA_ONLY/HOLD — NO PROMOTION.** This is not a strategy, a complete options surface, a historical economic TRAIN, or real execution evidence. No Frozen, legacy champion, paper/results, validation, holdout or order endpoints were changed or queried.

## What was actually verified

- [GitHub Actions 40064060169](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40064060169) succeeded. The workflow called the **first-party Deribit historical public options-trade API** for one **pre-fixed midpoint UTC day per each of the unchanged five R106 chronological TRAIN folds**, for both BTC and ETH. It used no post-TRAIN dates and no strategy returns.
- **10/10 first-party requests returned trades**: 100 historical option trades per request, **1,000 trade rows in total**. Every one of the 1,000 sampled trade rows included a non-null `iv` field; this establishes that original options-implied-volatility trade information exists in all five folds, **not** that a continuous executable IV surface exists.
- Distinct instruments in each 100-trade sample, BTC folds 1–5: **27, 34, 32, 48, 8**; ETH folds 1–5: **19, 51, 22, 25, 34**. The low BTC fold-5 count is a warning about sampling/market coverage, not an alpha signal.
- Original exchange JSON bytes, request metadata and SHA-256 digests are preserved in artifact **`v99-deribit-options-train-source-40064060169`** (artifact ID **12548785649**). An independent CI step re-opened all ten receipts, recomputed SHA-256 and verified every trade timestamp against its exact pre-fixed TRAIN day. **10/10 verified.**
- The archive endpoint was `https://history.deribit.com/api/v2/public/get_last_trades_by_currency_and_time` with `kind=option`, `include_old=true`. All ten responses had `has_more=true`: **100 is a request cap, not total trade coverage**. Do not treat the 1,000 records as complete source history.

## Critical-path decision

This is the first concrete newly evidenced **options-derived information family** after the exhausted OHLCV, positioning, taker, funding and basis families. It is a credible **source-feasibility lead**, not an economic edge or a finished engine.

**Next shortest useful step:** build a bounded, chronological, first-party **PIT options IV/skew/term-structure signal availability ledger** across the *entire TRAIN* (or reject early on pre-fixed coverage criteria), using expiry/strike/option type, trade timestamp and exchange-reported `iv`. Never infer unobserved bid/ask quotes from trades. If options are used only as an information source while trading spot/perps on OKX, Deribit option fill receipts are not required, but **original OKX account-specific fees/contract terms and conservative executable spot/perp fills** remain distinct deployment gates. If trading options, obtain contemporaneous executable bid/ask/depth and historical fee/margin/settlement provenance; otherwise do not score option execution.

After sufficient PIT coverage, **preregister one new, economically rational complete architecture before looking at its TRAIN returns**, with fixed five chronological folds, six regimes, both severe/supersevere paths, tail/drawdown and passive benchmarks, independent original-price-to-cash replay. Preserve the existing sealed validation [2023-10-01, 2024-01-18) and final holdout >=2024-01-18. Do not retune rejected C1/C2/D1/E1/F1/G1 or recycle an exhausted price feature.

**NO ROI. NO MODEL PROMOTION. NO REALIZED PAPER. NO ORDERS.**
