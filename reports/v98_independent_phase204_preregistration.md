# V98 Independent — Phase204 preregistration

## Hypothesis

A directional move that occurs during **relative realized-volatility expansion** and closes near the corresponding edge of its recent intrabar range may exhibit short-horizon continuation. This is distinct from Phase200 compression breakout and Phase203 directional-efficiency persistence: the state variable is expansion versus the asset's own lagged volatility baseline, while close-location supplies independent directional confirmation.

## Frozen causal construction

All features used for an entry at hour t are computed through t-1 only.

For each asset:

1. hourly log return `r`;
2. short realized volatility = rolling std of `r` over `rv_short` hours;
3. baseline realized volatility = rolling median of the short-RV series over 168 hours;
4. expansion ratio = short RV / lagged baseline RV;
5. close-location value (CLV) over the last bar = `(2*close-high-low)/(high-low)`, clipped to [-1,1];
6. directional displacement = close / close.shift(rv_short) - 1.

Long state at t: lagged expansion ratio >= threshold, lagged CLV >= +0.5, lagged displacement > 0.

Short state at t: lagged expansion ratio >= threshold, lagged CLV <= -0.5, lagged displacement < 0.

No cross-sectional ranking. No information from 2026+. No rescue after results.

## Frozen grid

Exactly 8 specifications:

- `rv_short`: 12h, 24h
- expansion threshold: 1.25, 1.75
- holding period: 3h, 6h

CLV threshold fixed at 0.5. Baseline window fixed at 168h. Equal-weight independent asset trades; no pyramiding within an asset while a position is active.

## Evaluation

Training-only chronological folds: calendar 2023, 2024, 2025. Validation/final holdout remain untouched.

Report for every spec/fold:

- return and max drawdown;
- Profit Factor, payoff, win rate, positive days;
- trade count/activity;
- funding and realistic base transaction costs;
- severe and supersevere cost scenarios;
- bear/bull/sideways decomposition;
- asset concentration and asset-level returns;
- tail diagnostics;
- deterministic/reproducibility hash and temporal-firewall invariant.

## Decision discipline

A family cannot be promoted because of one year, one asset or one regime. Base profitability must be broad across chronological folds and must retain meaningful robustness under cost stress. Excessive concentration, pathological tails, low activity, or material reproducibility/invariant failure rejects the candidate. If the frozen family fails, reject without threshold rescue, inversion, asset deletion or regime cherry-picking.
