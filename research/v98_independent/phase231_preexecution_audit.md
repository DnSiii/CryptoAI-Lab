# V98 Independent Phase231 — pre-execution audit

Status: PASS TO EXECUTION. Written before observing any Phase231 result.

- Preregistered family and exact 8-spec grid are unchanged.
- Decision `open(t)` reads `rv.iloc[i-1]`; rolling realized volatility therefore ends at `open(t-1)` and cannot use the `open(t-1)->open(t)` return.
- Ranking is deterministic `(realized_volatility, symbol)`; long low-vol / short high-vol exactly as frozen.
- Equal absolute side weights are dollar-neutral before sleeve overlap; gross exposure is normalized only above 1 and asserted <=1.
- Portfolio PnL uses lagged position against current open-to-open return; turnover costs are 7/14/28 bp and funding is point-in-time mapped to the first tradable hourly decision after publication.
- Folds are calendar 2023/2024/2025 only; loaders hard-fail on any timestamp >=2026-01-01. Holdout remains unopened.
- Required diagnostics include return, max drawdown, Profit Factor, payoff, win rate, positive days, tails, asset concentration/contribution, funding and lagged BTC regimes.
- Validator checks exact grid/folds/stresses, adverse cost monotonicity, deterministic payload SHA and the existing annual base gate. No rescue or post-result mutation is allowed.

Independent caution: trade-event tail diagnostics inherit the overlapping-sleeve approximation used in Phase230; portfolio accounting is authoritative for promotion/rejection. This limitation is frozen before results and cannot be selectively invoked after seeing outcomes.
