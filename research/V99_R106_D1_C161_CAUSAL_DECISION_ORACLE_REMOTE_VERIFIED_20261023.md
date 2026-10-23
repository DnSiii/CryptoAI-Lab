# V99 R106 D1 — C161 full TRAIN causal decision evidence oracle (2026-10-23 BRT)

**Decision: DATA_ONLY/HOLD — NO PROMOTION.** This is an independent source-structural negative-control improvement, not historical economics. No orders, paper/results publication, validation or final holdout.

## What was published and run

- Branch: `research/v99-r106-native-all-regime-engine`. Added three files only: `research/verification/independent_d1_c161_causal_decision_oracle.py`, `research/tests/test_v99_r106_d1_c161_causal_decision_oracle.py`, and `.github/workflows/v99-r106-d1-c161-causal-decision.yml`. GitHub compare `03d1bec...84693e8` reports exactly three **added** files, zero modified/deleted files.
- Commit `84693e83806e8328e900a8f42a095b0be9158877`. GitHub Actions run **39965405042** completed **SUCCESS**, job `120453841952`; log independently confirms **69 tests passed in 10.277s** and zero-promotion permission guard passed.
- Local independent preflight ran **6/6 new tests passed**. Remote CI runs the six new tests together with the prior C153–C160/full-TRAIN guard suites.

## New independent checks (synthetic fixture only)

- Reconstructs the exact **654** preregistered daily decision times after 168-hour warmup, across **15,864 TRAIN hours**. Independently binds **219,744** BTC/ETH feature asset-hours (654 × 2 × 168) to the same hourly journal used by C160; checks the **3,924** last-three-settlement comparisons (654 × 2 × 3).
- Recomputes BTC 168-hour 3×2 regime from actual journal-bound prices, verifies exact t−1 decision timestamps, and independently checks the *necessary* funding/basis/cost eligibility for **positive** pair exposure under severe and supersevere stress. Fee veto may remove an otherwise eligible exposure; therefore **exact C136 fee-veto decision reexecution is NOT claimed**.
- Adversarial tests reject a forged *early* feature bar even if t−1 matches, a forged last funding fix, positive exposure unsupported by settled funding, a fabricated regime agreed by both cost scenarios, and missing decision evidence. Full C160 account/funding/risk integration still executes.
- The flat artificial fixture has **zero modeled trades, zero model alpha, only 1/6 regimes**, and **0/5 positive folds**. It is a test fixture, **not a historical D1 strategy result or D1 rejection**.

## Hard scientific limitations

1. Self-declared `source='OKX'`, synthetic `FundingFix.announced_at`, hashes, and green GitHub CI **do not authenticate first-party historical OKX data**. Real historical funding announcement availability, actual settlements, native instrument terms, account-specific fee tier and executable fill/slippage provenance are still missing.
2. The C161 oracle verifies necessary eligibility and causal feature consistency, **not** the exact C136 native-fee veto, complete trade execution, or market-derived alpha. The C160 journal contains a self-declared C146 proof; C161 adds a separate independent feature check, but does not replace full C140–C147 deployment.
3. The original `C152` local integrated bundle is not yet deployed in full. No economic CI, authenticated ROI, independent real-TRAIN 5-fold robustness, six-regime coverage, tail/DD or four-passive-benchmark envelope is available. C1 and C2 remain permanently rejected; do not retune or reuse them as winners.
4. Validation `[2023-10-01,2024-01-18)` and final holdout `>=2024-01-18` remain sealed. Historical R106 holdout diagnostics are contaminated and must never be used for tuning.

## Next justified step

Deploy the remaining C140–C147/C152 model-only source **additively**, preserving all existing remote blobs; integrate the exact native-fee veto and full journal with C161/C160 and execute read-only CI. Independently anchor first-party OKX historical paired spot/perp, settled funding and availability, fee tiers, instrument specs and fills. If any required provenance is unavailable, **fail closed and remain DATA_ONLY/HOLD**. Only then execute one preregistered D1 historical TRAIN (five chronological folds, both cost scenarios, 3×2 regimes, tail/DD and four passive benchmarks), independent replay and formal freeze gates. No promotion based on synthetic or CI results.

**Frozen V16, Frozen V99, legacy champion, paper/results and historical records untouched by C161. NO PROMOTION.**
