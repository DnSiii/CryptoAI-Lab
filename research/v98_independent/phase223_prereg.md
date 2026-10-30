# V98 Independent Phase223 — preregistration

## Status and sequencing

**FROZEN BEFORE PHASE222 RESULT HARVEST.** Phase223 is a contingency family only. It may be executed only if Phase222 is mechanically rejected, or after Phase222 completes its already-preregistered robustness path. Phase222 evidence must not change any Phase223 setting below. Holdout >= 2026-01-01 UTC remains unopened.

## Hypothesis

**Idiosyncratic volatility-shock mean reversion.** After an asset experiences an unusually large completed 1h return relative to its own causal rolling volatility, the idiosyncratic component of that shock may partially reverse over the next few hours. This is scientifically distinct from Phase222's range-compression breakout continuation and Phase221's BTC-beta residual cross-sectional continuation: the signal is a within-asset standardized shock, traded contrarian, with an explicit market-direction filter rather than breakout/ranking logic.

## Frozen universe and evidence boundary

BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT. Existing V98 Independent canonical 1h data only. Training folds exactly calendar 2023, 2024, 2025. No loader, feature, report or selection step may inspect timestamps >= 2026-01-01 UTC.

## Causal feature definition

At decision hour t, all signal inputs end at t-1.

- `r1_i(t-1) = close_i(t-1)/close_i(t-2)-1`.
- `sigma_W_i(t-1)` = rolling standard deviation of completed hourly returns through t-1, with W exactly 168 or 336 hours and min_periods=W.
- `z_i(t-1) = r1_i(t-1)/sigma_W_i(t-1)`; if sigma is zero/non-finite, no trade.
- BTC market return uses the same completed `r1_BTC(t-1)`.
- Shock threshold K is exactly 2.5 or 3.5 absolute z.
- Direction is contrarian: z >= K -> short; z <= -K -> long.
- Market-direction filter: do not trade when the candidate shock has the same sign as BTC's completed 1h return **and** `|r1_BTC| >= 0.75%`; this preregistered filter is intended to exclude broad market jumps where idiosyncratic mean reversion is least plausible.
- Execute at open(t), the only current-bar field permitted. No high/low/close(t) enters the signal.

## Exactly eight frozen specs

Cartesian product only:

- W in {168,336}
- K in {2.5,3.5}
- H in {2,6} hours

Total exactly 8 specs. No additions/removals after any Phase223 result is observed.

## Portfolio and overlap

No same-asset overlapping position during H. Simultaneously active assets receive equal absolute notional; gross exposure <=1 at every hour, no leverage. Deterministic alphabetical ordering is bookkeeping only.

## Costs and funding

Use the established V98 Independent PIT funding accounting and the same frozen turnover cost schedules: base 7 bp, severe 14 bp, supersevere 28 bp per unit turnover. Funding is charged/credited only while exposure is actually open. Stress return must be monotone non-increasing base -> severe -> supersevere or the run is invalid.

## Required diagnostics

For every spec x fold x stress: compounded return, max drawdown, Profit Factor, payoff, win rate, positive-day fraction, trade count, clean asset-attributed trade p01/p05/p50/p95/p99 and worst/best trade, additive per-asset PnL contribution plus concentration, funding contribution, and bull/bear/sideways regime return/PF/MDD/payoff/win-rate/positive-days. Record deterministic payload SHA256 and require byte-identical rerun.

## Mechanical training gate

A spec is coherent only if base return >0 and base PF >1 in **each** of 2023, 2024, 2025. Zero coherent specs => `REJECT_FAMILY_NO_RESCUE`. Any coherent spec proceeds only to a separately preregistered robustness gate; holdout remains closed.

## Anti-overfit and reproducibility

No Phase221/222 result may tune W, K, H, market filter, universe, costs or folds. Rebuild training data independently; assert monotonic unique timestamps and cutoff firewall; assert exact eight specs; assert all feature inputs end at t-1; assert gross exposure <=1; execute twice; require identical payload/file hashes; verify stress monotonicity and metric domains. Any implementation correction after first result must invalidate that result for scientific decision until a corrected frozen rerun is completed.
