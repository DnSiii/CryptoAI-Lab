# V99 R106 Phase138 — Return-Innovation Decision

## Decision

**TRAIN_ALPHA_REJECT — permanent for the preregistered Phase138 hypothesis.**

Phase138 tested the preregistered cross-venue return-innovation continuation signal using OKX minus Binance 1h log returns, exact same-window 168h MAD normalization, cross-sectional demeaning, complete t-1 execution shift, L1 <= 1, chronological TRAIN-only evaluation, and four temporal folds.

## Observed TRAIN evidence

- active hours: 18,047
- ROI: -99.8526499%
- profit factor: 0.1474434
- max drawdown: 99.8528458%
- positive-hour ratio: 15.1050%
- robust mean excluding top 1%: -0.0003872860
- healthy temporal folds: 0 / 4

The hypothesis fails the first TRAIN alpha gate by a very large margin. Severe/supersevere costs, regime promotion, benchmark-envelope promotion, and holdout inspection are therefore not justified: additional downstream testing cannot rescue a signal that is already decisively negative before those gates.

## Integrity / causality audit

The workflow reproduced all Phase136 OKX hashes. OKX contained 18,672 rows per instrument. Binance TRAIN coverage was 100% for BTC/ETH/DOGE and 99.3573% for SOL/XRP; missing Binance observations were not filled, and the preregistered minimum coverage threshold was 98%.

Causality invariants passed: complete score shift = 1 hour, feature inputs strictly before TRAIN end, post-TRAIN targets = zero, max L1 = 1.0000000000000004, and common venue component removed by cross-sectional demeaning. Holdout rows used for feature construction/selection remained 0/0. V16 Frozen and V99 Frozen remained untouched.

## Scientific disposition

Reject Phase138 exactly as preregistered. No sign flip, parameter sweep, symbol substitution, selective asset removal, or threshold rescue is permitted from this result. Any future cross-venue experiment must be a separately preregistered and scientifically distinct hypothesis.
