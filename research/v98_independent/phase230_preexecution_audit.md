# V98 Independent — Phase230 pre-execution audit

Status: **AUDITED BEFORE RESULTS**.

## Frozen hypothesis and grid
Phase230 remains exactly the preregistered cross-sectional idiosyncratic-momentum family and exactly the eight preregistered specs. No economic parameter was changed after observing results; no Phase230 result existed when this audit was written.

## Causality audit
Decision is at `open(t)`. The evaluator computes open-to-open returns, subtracts the same historical hour's equal-weight cross-sectional market return, forms a trailing residual sum, and at decision index `i` reads only `signal.iloc[i-1]`. Thus the newest residual return ends at `open(t-1)` and bar `t` cannot enter the signal. Ranking ties are deterministic by symbol. No future beta/factor estimate is used.

## Exposure/accounting audit
Each decision creates equal long/short sleeves, target net zero, with gross normalized to <=1 under overlap. PnL uses lagged held weights against open-to-open returns; turnover costs are charged from absolute weight changes at frozen 7/14/28 bp. Funding is point-in-time and aligned to held side through lagged weights. The training firewall rejects any price/funding timestamp >= 2026-01-01.

## Evaluation invariants
Chronological folds are calendar 2023/2024/2025. Required outputs include return, max DD, PF, payoff, win rate, positive days, trades, tails, worst/best trade, asset contribution/concentration, funding contribution and lagged BTC bull/bear/sideways diagnostics. Validator requires stress-return monotonicity and verifies deterministic payload SHA256. Two byte-identical executions remain required before scientific acceptance.

## Anti-overfit decision rule
No asset/year/regime may be removed to rescue a failure. No thresholds may be weakened. Zero survivors means `REJECT_FAMILY_NO_RESCUE`; any survivor requires further independent accounting/causality audit before promotion. Holdout 2026+ remains unopened.
