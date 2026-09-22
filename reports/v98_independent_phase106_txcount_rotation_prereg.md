# V98 Independent Phase106 — relative transaction-throughput rotation

PRE-REGISTERED after Phase105 PASS_DATA_ONLY and before any Phase106 alpha/PnL.

Status at preregistration: **UNEVALUATED**.

Economic hypothesis: relative blockchain transaction throughput may lead relative demand/attention between BTC and ETH. This is distinct from Phase104's absolute active-address regime: the observable is `TxCnt`, and the portfolio is a dollar-neutral BTC-vs-ETH rotation based on relative 28-day throughput growth.

Frozen design:
- source: Coin Metrics Community API;
- metric: `TxCnt`, daily;
- assets: BTC and ETH only;
- signal information set: completed UTC days only;
- strict lag: latest usable metric is D-1;
- score: 28-calendar-day log change in `TxCnt` (one fixed four-week horizon chosen before PnL to reduce weekday seasonality);
- rebalance: daily at 00:00 UTC;
- portfolio: long the asset with higher score and short the other, equal absolute weights;
- gross cap: 0.75 (0.375 long + 0.375 short), dollar-neutral by construction;
- no threshold, alternate horizon, sign search, asset subset, regime filter, stop, cadence search or rescue is permitted.

Training boundary: existing V98 training folds through 2025 only. Validation remains closed. Phase083 and all opened/future holdout observations are forbidden for selection. V16 and V99 are excluded.

Frozen gates:
1. aggregate BASE return > 0;
2. aggregate BASE daily PF > 1.10;
3. aggregate BASE max drawdown >= -35%;
4. aggregate BASE worst day >= -12%;
5. every chronological fold (2023, 2024, 2025) return > 0 and daily PF > 1.02;
6. severe and supersevere each return > 0 and daily PF > 1.00;
7. largest absolute asset contribution share <= 60%;
8. top-10 absolute daily-return concentration <= 60%.

Report all requested metrics regardless of gate outcome: return/CAGR, worst/best day, p01/p05/CVaR5, DD, PF, payoff, win rate, positive/negative days, turnover, gross/net exposure, folds, costs/funding stresses, regimes, concentration, tails, asset contribution and reproducibility hashes.

Any failed mandatory gate => **REJECT_NO_RESCUE**. PASS_TRAINING may authorize a separately preregistered validation phase; it does not authorize future holdout access.
