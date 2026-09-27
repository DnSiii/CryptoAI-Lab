# V99 R106 cross-venue failure audit — Phase149 through Phase156

Date: 2026-09-27. Scope is TRAIN evidence only; no holdout inspection.

## Evidence through Phase156
The recent cross-venue OHLC-derived reversion family has repeatedly failed before downstream promotion. Phase156 body-fraction divergence is a decisive reject: TRAIN ROI -99.6637%, PF 0.1793, MaxDD 99.6637%, robust mean excluding top 1% -0.03460%/h, positive-hour ratio 17.08%, and 0/4 healthy temporal folds. Its four fold ROIs are approximately -74.30%, -74.66%, -76.83%, and -77.71%; therefore failure is temporally broad rather than a single-period tail accident.

Phase156 source/invariant checks remained clean: all Phase136 OKX hashes reproduced, valid/aligned coverage remained above the preregistered 98% gate, no invalid-bar imputation occurred, normalizer history excluded the current hour, complete score was shifted one hour, post-TRAIN targets were zero, max L1 was <=1, and V16 Frozen/V99 Frozen were untouched.

## Mechanism interpretation
The repeated near-total-loss outcomes in the recent family, together with 0/4 healthy folds, are inconsistent with a fragile edge ruined only by one exceptional tail. They indicate that continuously normalizing cross-venue candle-geometry disagreement and trading it as unconditional next-hour reversion has no acceptable TRAIN edge under the severe-cost execution contract. Trading almost every eligible hour (Phase156: 17,870 active hours) compounds a persistently negative hourly expectancy and costs.

This is a family-level warning, not permission to sign-flip: direction was preregistered, so failed reversion variants remain permanently rejected. Momentum would require a separately motivated preregistration, not post-hoc inversion.

## Scientific consequence
Do not tune Phase149–156 thresholds/lookbacks or rescue their signs. Phase157 is allowed only because CLV is a distinct range-location geometry (close relative to both extrema, independent of open), and it was preregistered before its PnL. If Phase157 reproduces the same broad negative fold structure, the next step should leave unconditional cross-venue OHLC geometry rather than continue making cosmetic algebraic variants; priority should move to genuinely orthogonal data or a separately preregistered state-conditioned mechanism.
