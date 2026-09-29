# V99 R106 — Phase182 causal feature audit

Date: 2026-09-29
Status: TRAIN-ONLY / HOLDOUT UNTOUCHED

## Evidence harvested

The Phase182 pair-integrity workflow for commit `119eceb673178e14b93415541485e445afc6322e` completed SUCCESS. This establishes the integrity-gate tests, not alpha validity.

The canonical PIT48 manifest reports BTCUSDT and ETHUSDT both beginning 2020-01-01 00:00 UTC, 57,696 rows through 2026-07-31 23:00 UTC, and zero missing hours. Phase182 itself remains firewalled at 2024-01-18 and must never consume the manifest's later rows during TRAIN research.

## Independent causality audit

The preregistration says every decision at t must depend only on information ending at t-1. A common implementation error would be computing a rolling 24-bar statistic ending at t and shifting only the final signal. Phase182 therefore implements the lag structurally inside the feature builder: all one-bar returns, 24-bar sums, realized-volatility ratio, volume shock and interaction end at t-1.

The builder refuses input unless the pair DATA gate passes. It emits source hashes and a feature-file hash. Warm-up rows are dropped rather than imputed.

Dedicated invariants mutate a future source bar and the decision bar itself, requiring all earlier/current decision features to remain byte-identical. A second invariant requires repeated builds to be byte-identical.

## Scientific boundary

Passing these invariants authorizes only deterministic TRAIN feature construction. It does not authorize holdout access or promotion. The next gate is a single frozen-sign TRAIN alpha/evaluation using the already preregistered feature family, chronological folds, unchanged severe/supersevere costs, regime matrix, benchmark envelope, and mandatory tail/concentration diagnostics. No window, sign, threshold or feature deletion may be chosen after PnL inspection.
