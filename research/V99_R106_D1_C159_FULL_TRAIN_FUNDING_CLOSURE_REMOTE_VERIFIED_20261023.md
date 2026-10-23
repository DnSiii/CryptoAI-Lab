# V99 R106 D1 — C159 full-window funding schedule closure (2026-10-23 BRT)

**Decision: DATA_ONLY/HOLD — NO PROMOTION.** No economic TRAIN executed; no exchange-authenticated ROI, validation, final holdout, real orders or paper publication. C1/C2 and other rejected strategies remain rejected.

## Implemented and independently checked

- Integrated the previously local C132 independent hourly funding journal-vs-schedule audit and C133 full-TRAIN closure modules additively on `research/v99-r106-native-all-regime-engine`, without changing D1's preregistered strategy or immutable paths.
- Added 8 C159 adversarial synthetic tests: complete fixture; missing ETH settlement; duplicate event; shifted BTC schedule; non-8h cadence; partial TRAIN; validation-hour injection; missing one schedule row.
- C133 requires exactly **15,864 UTC TRAIN hours** [2021-12-09, 2023-10-01), **1,983 8-hour fixes per asset** and **3,966 two-asset funding events**, five chronological folds **[3172, 3173, 3173, 3173, 3173]**. C132 rejects missing, extra, duplicated, unordered, shifted or out-of-window events.
- Independent local arithmetic confirmed TRAIN duration = 15,864 hours and 15,864 / 8 = 1,983 fixes per asset; local C159 test suite **8/8 green**.
- GitHub Actions **39948518577** completed **SUCCESS** at commit `b555839a5b93b818df6880df02188d9ef720ec6d`: **57/57 source-only tests green**, including previous D1 source checks and the new eight negative controls. Source-only workflow: `.github/workflows/v99-r106-d1-c159-full-funding-closure.yml`.

## Limitations and binding scientific gate

- These are **synthetic fixture** timestamps and journal rows, NOT independent OKX provenance. Exact schedule count and successful CI are **not** authenticated funding settlements, account-level fee tiers, native fills, executable lots, true market returns or alpha. The audit returns `schedule_source_authenticated=False`, `account_settlement_authenticated=False`, `historical_roi_authorized=False`.
- C133 enforces the *frozen preregistered* 8-hour funding cadence. If first-party historical instrument terms contradict that cadence, **fail closed; do not silently reinterpret 1h/2h/4h settlements as 8h or retune the hypothesis**.
- The full C152 hourly model journal, t-1 feature/funding binding and native-fee/fill bridge are **not yet fully integrated and economically exercised remotely**. C159 does not fix that.
- First-party historical paired BTC/ETH OKX spot/perp bars, instrument specifications, as-of account-specific fee tier, actual settled funding and execution evidence remain unverified as a complete historical TRAIN set. Prospective collector receipts alone do not fill this gap.

## Next justified work

1. Integrate remaining C152 modules **additively**, with immutable paths untouched, and wire C132/C133 funding closure into the end-to-end journal and independent account oracle.
2. Verify **independently anchored** historical OKX native terms/funding/fees/fills for the exact TRAIN partition; if unavailable, continue source and accounting work and keep economics fail-closed.
3. Only after complete source proof, execute the **single preregistered D1** two-scenario economic TRAIN; report five folds, six regimes, tail concentration, max DD, native lots and passive benchmark envelope. Freeze only if formal gates pass. Sealed validation [2023-10-01, 2024-01-18) and final holdout >=2024-01-18 remain unopened.

**NO PROMOTION; no strategy tuning, no orders, no historical claims, no dashboard profit advertising.**
