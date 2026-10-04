# V98 Independent Phase230 — independent accounting/integrity audit

Status: PRE-HARVEST. No Phase230 result was inspected to write this audit.

## Scope
Frozen family: cross-sectional idiosyncratic momentum. This audit checks decision timing, return attribution, exposure, turnover/costs, funding timing, diagnostics, folds, and holdout firewall without changing any economic parameter.

## Findings
1. **Decision causality:** at decision `open(t)=idx[i]`, ranking reads `signal.iloc[i-1]`. The residual at row `i-1` is the return `open(i-2)->open(i-1)`, so no `open(t)` price change enters ranking.
2. **PnL timing:** a weight written at row `i` is applied through `w.shift(1) * rr`; therefore the first market return earned is `open(i)->open(i+1)`, after the decision. This is causal.
3. **Turnover/cost:** `abs(diff(weight)) * cost` is charged when weights change. Costs are frozen at 7/14/28 bp and severe/supersevere must degrade monotonically versus base, subject only to numerical tolerance.
4. **Funding PIT:** funding is mapped to the next hourly decision boundary and charged to the previously held weight (`w.shift(1)`), avoiding use of a funding print before it is observable. Funding data are firewalled `<2026-01-01`.
5. **Exposure:** overlapping sleeves are deterministically normalized whenever gross exceeds 1; invariant requires gross <= 1 + 1e-12.
6. **Chronology:** folds remain calendar 2023, 2024, 2025. No 2026+ price/funding row is permitted.
7. **Portfolio metrics:** return, max drawdown, Profit Factor, payoff, win rate and positive days are computed from authoritative portfolio hourly PnL.
8. **Regimes:** BTC 168h return is shifted by one row before regime classification; regime labels therefore use information available before the evaluated hourly return.
9. **Concentration:** per-asset portfolio PnL contributions and max absolute contribution share are recorded.
10. **Tail caveat:** `trade-event` tail diagnostics are explicitly approximate because `pp[a]` contains aggregate asset PnL from all overlapping sleeves, not isolated sleeve PnL. These tails are useful pathology indicators but MUST NOT be interpreted as exact per-trade economics or used alone for promotion. Portfolio accounting remains authoritative.

## Mechanical decision discipline
No parameter, fold, cost, asset, regime threshold, or gate is changed after results. Phase230 may advance only through the preregistered validator. If it fails, reject the family without rescue. If it passes, proceed to deeper independent accounting/tail/concentration stress before any holdout access.
