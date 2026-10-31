# V98 Independent OV — FROZEN REJECTION (2026-10-31)

**Binding decision: REJECT_OV_TRAINING. OV is not a champion.** No sign, window, threshold, weighting, cost, exposure or economic-gate retuning to rescue OV. No V14/V15/V99 internals or benchmarks, 2026+, XRP, contaminated Phase083 holdout, V16/V99 Frozen or paper/live state touched.

## Immutable provenance
- Preregistration before any OV PnL: commit `a01fed933685d9d0fb92e16c752963e8f8f52b5f`.
- Original full physical workflow: [run 41240698895](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41240698895), pinned code `05feaa530918ff4ad1ce1ac5136350de2093a12b`. Workflow marked failure **intentionally** after completing all 30 cells because binding economics failed, not because of a software crash.
- Full original `OV_RESULT_JSON` is frozen as `ov_full_training_frozen_result_20261031.json`; original Actions artifact ID 13057660773. Clean-4 2022-25 exposed exploratory training: 27,048 hours, 13,524 signed native-rate funding events, 157 weekly decisions, 26,303 settled physical hours. 2025 is exposed, NOT virgin validation. Exact event markPrice remains unavailable.

## Original modeled economics (OV_full, carried-before-fill; initial USD10,000)
| Tier | CAGR | Max drawdown | Gross turnover USD | Final equity USD | Funding cash USD |
|---|---:|---:|---:|---:|---:|
| Base (4+2bps) | **+0.9601%** | -41.6625% | 1,147,398.97 | 10,290.87 | -737.53 |
| Severe (10+10bps) | **-4.0127%** | -46.5242% | 1,063,867.74 | 8,843.61 | -699.27 |
| Supersevere (15+20bps) | **-9.0013%** | -51.1674% | 983,019.22 | 7,534.90 | -661.88 |

Base annual modeled returns: 2023 +33.8580%, 2024 -15.2677%, 2025 -9.2683%. Severe annual: +27.2891%, -19.2937%, -13.9143%. Base 448/1096 positive days. These are exploratory historical model figures with hourly conservative mark envelopes, NOT exact tick-level native settlement, virgin holdout, verified future returns, or paper/live results.

## Binding gate and independent reconciliation
- **30/30 physical cells settled**, 3 cost tiers × 2 funding orders × 5 books.
- Independent signal/allocator oracle: **157 decisions × five books**, zero mismatches, max weight error zero; 111 propagation, 43 transition, 3 panic regimes.
- Independent hourly cash identity: **26,303 hours**, zero mismatches, max cash error ~1.82e-12 USD. Independent fill/fee/slippage/funding oracle: **171 net fill events**, 3,287 funding hours, zero mismatches.
- **32 economic gate failures** in original frozen result. Base and severe CAGR both fail; base and severe turnover exceed USD1m; severe drawdown breaches -45%; 2024/2025 severe annual returns negative. Opportunity marginal is exactly zero (no realized marginal contribution), Relative Value fails positive marginal and 2024/2025 annual contribution, Stress/Recovery marginal is negative.
- Full-minus-ablation base log wealth: Opportunity 0.000000; Relative Value +0.013411 (<+0.02 prereg gate); Stress/Recovery -0.001540. Severe: Opportunity 0.000000; Relative Value -0.000393; Stress/Recovery -0.002441. No cosmetic module rescue.

## Delivery blockers and next move
1. No complete seven-slot V98 has passed internal economic gates; OV remains permanently rejected.
2. Exact 13,524 official Binance USD-M `fundingRate` event `markPrice` objects (BTC/ETH/BNB/SOL, Dec-2022–Dec-2025) with original raw responses, request/response metadata, hashes, and independently verified source transport remain missing. Official GitHub runner access previously returned HTTP451/202/400/timeouts. Authorized exchange export with verifiable chain of custody is an alternative. Conservative hourly official mark OHLC bounds are not exact settlement marks.
3. Separate untouched prospective chronological validation and later final holdout must follow any *new* internally viable candidate; exposed 2025 and contaminated Phase083 are ineligible. External benchmarks remain sealed until that point.

**Next architectural research:** reject BTC-led propagation as formulated; investigate a genuinely distinct economic mechanism, without tuning OV on observed losses. No operation real or paper authorization.

## Independent post-freeze gate re-derivation
[GitHub Actions 41240861232](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41240861232) **PASS_INDEPENDENT_OV_FROZEN_REJECTION_AUDIT_NOT_ENGINE**. A separate read-only auditor, importing neither the primary strategy nor the physical runner, verified all 30 unique physical cells, recomputed all **32** binding economic failures, independently reconciled recorded marginal log growth (maximum discrepancy 1.26e-16), and checked 157 signal decisions / 26,303 hourly cash receipts. This certifies rejection arithmetic only; it is **not** an approved engine, exact funding source, or future validation.
