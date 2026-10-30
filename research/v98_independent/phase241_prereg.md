# V98 Independent Phase241 preregistration

## Hypothesis
A genuinely orthogonal family to residual moments/persistence: cross-sectional **volume-price dislocation**. Assets whose lagged abnormal quote-volume impulse is unusually high relative to their own history while lagged price return fails to confirm the impulse may subsequently mean-revert relative to peers. This uses price/volume microstructure information, not residual distribution shape.

## Information firewall
- Training/evaluation only through 2025-12-31 23:00 UTC; 2026+ remains untouched.
- Every decision for open(t) uses features ending at t-1 or earlier.
- No V99 evidence, files, reports, workflows, state, or tuning.
- No sign flip or rescue after results.

## Frozen construction
For each asset and hour u:
1. `r24(u) = close(u)/close(u-24)-1`.
2. `lv(u)=log1p(quote_volume(u))`.
3. Abnormal volume `av(u)=(lv(u)-rolling_median(lv, vw).shift(1))/rolling_MAD(lv, vw).shift(1)`, with MAD floor 1e-9.
4. At decision t, use `av(t-1)` and `r24(t-1)` only.
5. Dislocation score = cross-sectional zscore(av) * -cross-sectional zscore(r24). Positive means abnormal activity opposing/unsupported by price confirmation.
6. Rank score cross-sectionally; long top k and short bottom k, equal-weight, dollar-neutral, gross <=1.
7. Hold H hours; rebalance each hour. No regime gating.

## Frozen grid
- volume window `vw ∈ {168, 336}` hours
- `k = 1`
- holding `H ∈ {4, 8}` hours
- return confirmation horizon fixed 24h
Total 4 specs. Small grid is deliberate anti-overfit discipline.

## Evaluation
Chronological annual folds: 2023, 2024, 2025. Include point-in-time funding and realistic trading costs exactly as current V98 decision-grade convention: base 7 bp, severe 14 bp, supersevere 28 bp per unit turnover.

For every spec/year/cost report: return, max drawdown, Profit Factor, payoff, win rate, positive days, turnover, funding contribution, asset PnL/concentration, daily tail quantiles, best/worst day, and bear/bull/sideways diagnostics. Require deterministic byte-identical rerun and independent validator.

## Mechanical gate
No promotion unless a frozen spec has, in **every** 2023/2024/2025 fold: base return >0, base PF >1, base max drawdown >= -35%, base positive days >50%, severe return >0 and severe PF >1. Supersevere is mandatory diagnostic/stress evidence, not a tunable gate. Any family-wide failure is `REJECT_FAMILY_NO_RESCUE`.

No opened holdout, threshold search, asset deletion, sign flip, regime rescue, or parameter expansion is allowed after observing Phase241 results.
