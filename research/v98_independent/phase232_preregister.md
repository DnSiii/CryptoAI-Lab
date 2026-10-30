# V98 Independent Phase232 — preregistration

Status: FROZEN BEFORE ANY PHASE231 RESULT. This family is scientifically distinct and MUST NOT be altered using Phase231 outcomes.

## Hypothesis
Cross-sectional **lagged market-beta dispersion relative value**: estimate each altcoin's rolling beta to BTC using only returns known before the decision. Test whether unusually high-beta assets subsequently mean-revert relative to unusually low-beta assets over short horizons. Ranking uses beta magnitude only, not realized-volatility rank or return momentum.

## Information set / execution
- Universe fixed: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT.
- Decision at `open(t)` may use open-to-open returns ending no later than `open(t-1)`.
- Rolling beta is covariance(asset,BTC)/variance(BTC), computed strictly on lagged hourly returns with frozen lookback.
- Rank deterministically by `(beta, symbol)`; long lowest-beta `k`, short highest-beta `k`, equal absolute weights, dollar-neutral, gross <= 1.
- Hold from `open(t)` for frozen H hours with deterministic overlapping sleeves and gross normalization only above 1.
- No regime filter, asset exclusion, sign flip, threshold rescue, or post-result parameter change.

## Frozen grid — exactly 8 specs
`(lookback_hours, k_each_side, hold_hours)`:
- (72,1,4), (72,1,8)
- (168,1,4), (168,1,8)
- (336,1,4), (336,1,8)
- (168,2,4), (336,2,8)

## Evaluation
Chronological untouched training folds: calendar 2023, 2024, 2025. Holdout 2026+ remains unopened. Funding must be point-in-time and causal. Costs are frozen at base 7 bp, severe 14 bp, supersevere 28 bp using turnover accounting.

For every spec/fold/stress record total return, max drawdown, Profit Factor, payoff, win rate, positive days, tails, asset contribution/concentration, funding contribution, and lagged BTC bull/bear/sideways regimes. Require deterministic reproduction, data firewall, gross-exposure invariant, cost monotonicity, and independent validation.

## Gate
Use the existing V98 mechanical annual discipline with no cherry-picking and no rescue. A spec can advance only if it satisfies the frozen validator across all chronological folds at base cost and remains economically coherent under severe/supersevere stress. If no spec survives: `REJECT_FAMILY_NO_RESCUE`.

Phase231 results may determine only whether Phase232 is executed next; they may not alter this frozen hypothesis or grid.
