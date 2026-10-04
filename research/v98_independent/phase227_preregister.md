# V98 Independent Phase227 — preregistration

Status: **PREREGISTERED / NOT EXECUTED**.

## Hypothesis

Test a genuinely distinct mechanism: **cross-sectional short-horizon reversal after market-neutral residual displacement**, without using volume, funding, or Phase226 momentum sign as a selector. A large idiosyncratic displacement relative to a trailing BTC beta may partially mean-revert over the next few hours because temporary crypto-specific liquidity imbalance can overshoot fair relative value.

This is scientifically distinct from Phase226: Phase226 tested persistence in the direction of residual displacement; Phase227 freezes the opposite economic mechanism *before any Phase227 result exists*. It is not a rescue of Phase226: no Phase226 cell, asset, regime, threshold, tail, or year is used to choose Phase227 parameters.

## Frozen causal construction

Universe: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT. Hourly canonical futures data and realized PIT funding snapshots already namespaced for V98. Data firewall: timestamps must be `<2026-01-01`; 2026+ remains unopened.

At decision time for `open(t)`, all signal inputs end at `t-1`. Estimate each alt's BTC beta from the trailing 720 completed hourly returns, shifted one hour. Compute residual return over a frozen lookback W ending at t-1. Rank absolute residual displacement cross-sectionally; only extreme residuals qualify. Trade **against** residual sign at open(t), exit open(t+H). BTC is benchmark only, not a candidate leg. No overlapping position in the same asset. Portfolio gross exposure <=1; new cohorts receive only remaining gross capacity and existing cohorts are never retrospectively rescaled.

Exactly eight frozen specs: W in {24,72} hours × cross-sectional tail q in {0.010,0.020} × H in {4,8} hours. No extra variants after results.

## Accounting and gates

Chronological evaluation folds: calendar 2023, 2024, 2025. Costs round-trip: base 7 bp, severe 14 bp, supersevere 28 bp. Realized funding is charged/credited only when its timestamp falls inside an actually held position, using PIT funding records; funding is accounting only, never a signal.

For every spec/year/cost report return, max drawdown, Profit Factor, payoff, win rate, positive days, trade count, funding contribution, per-asset contribution/concentration, trade tails p01/p05/p50/p95/p99 and worst/best trade. Report bull/bear/sideways diagnostics without using regimes for selection.

A spec may survive only if, under base cost, **each** of 2023/2024/2025 has return >0, PF >1, positive-days >50%, and >=30 trades. Severe/supersevere are mandatory robustness evidence and must deteriorate monotonically where costs apply; they cannot be used to tune parameters. Reproducibility requires two byte-identical deterministic payloads plus an independent validator/invariant check.

## Anti-overfit disposition

If zero frozen specs pass, decision is `REJECT_FAMILY_NO_RESCUE`. No asset deletion, regime rescue, threshold refinement, year exclusion, sign flip, or holdout opening is allowed. If a frozen spec survives, it advances only to the next preregistered validation gate; it does not become champion merely from this screen.
