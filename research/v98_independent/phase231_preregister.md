# V98 Independent Phase231 — preregistration

Status: FROZEN BEFORE ANY PHASE231 RESULT. This is a scientifically distinct fallback hypothesis and MUST NOT be altered using Phase230 outcomes.

## Hypothesis
Cross-sectional **volatility-dispersion relative value**: when one asset's recent realized volatility is unusually high relative to the five-asset cross-section, short the highest-volatility asset and long the lowest-volatility asset(s), market-neutral, testing whether idiosyncratic volatility expansion mean-reverts over short horizons. This is distinct from Phase230 directional residual momentum: ranking uses only lagged realized volatility magnitude, not return sign or momentum.

## Information set / execution
- Universe fixed: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT.
- Decision at `open(t)` may use returns ending no later than `open(t-1)`.
- Realized volatility = rolling standard deviation of hourly open-to-open returns over frozen lookback.
- Rank assets deterministically by `(realized_volatility, symbol)`.
- Long lowest-volatility `k`, short highest-volatility `k`; equal absolute weights, dollar-neutral, gross <= 1.
- Hold from `open(t)` for frozen H hours using deterministic overlapping sleeves; normalize only if overlap would make gross > 1.
- No regime filter, asset exclusion, threshold rescue, or post-result parameter change.

## Frozen grid — exactly 8 specs
`(lookback_hours, k_each_side, hold_hours)`:
- (24,1,4), (24,1,8)
- (72,1,4), (72,1,8)
- (168,1,4), (168,1,8)
- (72,2,4), (168,2,8)

## Evaluation
Chronological untouched training folds: calendar 2023, 2024, 2025. Holdout 2026+ remains unopened. Funding must be point-in-time and causal. Round-trip/turnover accounting must use realistic base 7 bp, severe 14 bp, supersevere 28 bp costs exactly as prior V98 decision-grade phases.

For every spec/fold/stress record total return, max drawdown, Profit Factor, payoff, win rate, positive days, tails, asset contribution/concentration, funding contribution, and lagged BTC bull/bear/sideways regimes. Require deterministic reproduction and firewall/invariant checks.

## Gate
Use the existing V98 mechanical annual discipline: no cherry-picking and no rescue. A spec can advance only if it satisfies the frozen validator requirements across all chronological folds at base cost and remains economically coherent under severe/supersevere stress. If no spec survives, `REJECT_FAMILY_NO_RESCUE`.

Phase230 results may determine only whether Phase231 is executed next; they may not alter this frozen Phase231 hypothesis or grid.
