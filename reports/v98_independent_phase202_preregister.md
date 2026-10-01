# V98 Independent — Phase202 preregistration

Status: **FROZEN BEFORE RESULTS**.

## Hypothesis
A purely price-based, time-series range-position reversal may capture short-horizon exhaustion without relying on volume-shock continuation or cross-sectional quantiles. For each symbol independently, compute prior-bar position inside a trailing high/low range. Extreme upper-range position predicts a short reversal; extreme lower-range position predicts a long reversal.

## Causality
At decision hour t, every feature must be computed using observations available no later than t-1. No centered windows, future extrema, future volume, or same-bar close-to-close signal leakage. Entry/return accounting must begin only after signal availability.

## Frozen grid
- trailing range: 24h, 72h
- extreme threshold: 0.05, 0.10
- holding period: 3h, 6h
- Cartesian grid: 8 specifications total.
- No post-result threshold additions, sign inversion, parameter rescue, or selective symbol deletion.

## Evaluation
Use only canonical V98 Independent training data through 2025-12-31. Chronological folds are 2023, 2024, 2025. Validation/final holdout are forbidden unless a candidate later satisfies the existing promotion discipline.

For every spec report base, severe and supersevere execution costs; funding where available; return, max drawdown, Profit Factor, payoff, win rate, positive days, turnover/activity; bear/bull/sideways regimes; per-symbol PnL/concentration; top-gain and bottom-loss tail concentration. Reject zero-activity specs.

## Gates
A candidate may only advance if economics are positive and coherent across chronological folds, PF is robust rather than driven by a narrow tail/regime/symbol, drawdown is acceptable relative to return, and severe/supersevere stresses do not reveal cost-only profitability. Reproducibility and temporal/data invariants are mandatory.

Phase201 evidence is not used to tune this grid beyond motivating a scientifically distinct price-only family. V16 Frozen, V99 Frozen/research/workflows/reports/paper and all holdout state remain out of scope.
