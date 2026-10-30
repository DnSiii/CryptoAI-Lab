# V98 Independent — Phase219 preregistration

## Family
Funding-extreme post-settlement mean reversion.

## Scientific hypothesis
Perpetual funding contains an orthogonal positioning/crowding signal. After an unusually extreme *observed* funding settlement, crowded positioning may unwind over the next few hours. Test whether trading against the sign of an extreme funding observation has stable net edge after realistic costs. This family is distinct from Phase218 realized-volatility term structure and does not use V99 evidence.

## Causality / timing
For each non-BTC asset independently, use only funding observations whose settlement timestamp is strictly known by decision time. At an hourly decision timestamp `t`, the latest eligible funding value must have `fundingTime <= t-1h`; no forward-filled future settlement is allowed. Rolling statistics are computed only from eligible prior funding observations. Entry begins at `t`; returns before `t` cannot enter PnL. Missing funding means no signal. Price returns use `pct_change(fill_method=None)`.

## Frozen grid — exactly 8 specs
Cartesian product:
- funding z-score lookback: 90 or 270 prior funding observations (approximately 30d / 90d at 8h cadence)
- absolute z threshold: 1.5 or 2.0
- hold: 4h or 8h

`SPECS = [(L,Z,H) for L in (90,270) for Z in (1.5,2.0) for H in (4,8)]`

Signal: if latest eligible funding z-score >= +Z, short that asset; if <= -Z, long that asset; otherwise flat. No BTC leg. Equal risk/notional across simultaneously active eligible assets, total gross exposure capped at 1.0. Do not overlap a new position in an asset while its prior hold is active.

## Data and folds
Use only V98 Independent canonical hourly prices and V98 Independent PIT funding already acquired for ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT. Training evaluation is chronological calendar folds 2023, 2024, 2025. Data firewall is `<2026-01-01`. Validation/final holdout remains unopened unless the frozen promotion gate is passed.

## Execution realism
Retain the established V98 Independent base, severe and supersevere round-trip cost schedules without modification. Charge realized PIT funding during every open position according to position sign and settlement timestamp. No favorable funding assumption, no fee rebate assumption, no same-bar lookahead.

## Required outputs
For every spec × fold × stress: net return, max drawdown, Profit Factor, payoff, win rate, positive days, trade count, p01/p05/p50/p95/p99 trade tails, best/worst trade, max asset concentration, funding contribution by asset, asset returns, and bull/bear/sideways regime diagnostics. Preserve deterministic serialization and reproducibility hash.

## Frozen training promotion gate
A spec is training-coherent only if, in each of 2023/2024/2025 under base costs, return > 0 and Profit Factor > 1. Stress returns must deteriorate monotonically base >= severe >= supersevere. Any later validation gate must be declared before opening validation/holdout.

## Anti-overfit decision rules
- Zero coherent specs => reject entire family; no sign inversion, asset exclusion, regime rescue, threshold extension, or nearby parameter search.
- A coherent spec may advance only by the frozen deterministic rule; no discretionary cherry-picking.
- Phase219 evidence cannot alter earlier rejected families.
- V99/V16 evidence, workflows, reports and paper state are out of scope and must remain untouched.
