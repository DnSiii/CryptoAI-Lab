# V98 Independent Phase239 — pre-execution audit

Status: completed before observing any Phase239 performance result.

## Preregistration-to-code audit
- Frozen family remains residual sign persistence; no magnitude information is used in the statistic.
- Grid is exactly beta {168,336} x persistence {72,168} x k=1 x H {4,8} = 8 specs.
- Residual uses `beta.shift(1)`, so beta for residual u is estimated without u.
- Sign persistence is `sign(resid[u])*sign(resid[u-1])`, rolling mean; decision at open(t) reads `signal.iloc[i-1]` only.
- Long highest persistence / short lowest persistence; no post-result sign flip.
- Gross exposure is normalized to <=1 and asserted.
- Folds are calendar 2023/2024/2025; data >=2026 is rejected by price and funding firewalls.
- Funding is charged PIT against lagged signed held exposure.
- Costs remain base/severe/supersevere = 7/14/28 bp under the existing turnover accounting convention.

## Diagnostics retained
Return, max drawdown, Profit Factor, payoff, win rate, positive days, turnover L1, event count, hourly tails, best/worst day, asset/funding contribution, max asset concentration, and lagged-BTC bull/bear/sideways diagnostics.

## Mechanical gate
Independent validator requires exact grid/folds/costs/finite diagnostics and cost monotonicity. Annual gate is unchanged: each calendar year must have base return >0, PF >1, DD >-35%, positive days >50%, and positive severe and supersevere returns. No asset/parameter/regime rescue is allowed.

Conclusion: implementation is eligible for decision-grade execution; Phase239 performance remains unobserved at this audit point.
