# V98 Independent Phase109 — fee-burden rotation

PRE-REGISTERED after Phase108 PASS_DATA_ONLY and before any Phase109 alpha/PnL.

Status: **UNEVALUATED**.

Economic hypothesis: relative fee burden can proxy relative willingness to pay for scarce blockspace / network settlement demand. To make BTC and ETH dimensionally comparable without market prices, daily native fees are normalized by native current supply. The hypothesis predicts that the asset with the stronger recent increase in this dimensionless fee burden should outperform the other.

Frozen design:
- source: Coin Metrics Community API;
- assets: BTC and ETH only;
- raw metrics: `FeeTotNtv`, `SplyCur`;
- daily fee burden: `FeeTotNtv / SplyCur`;
- information timing: completed UTC days only, strict D-1 lag;
- score: log ratio of the most recent 7-day sum of fee burden to the prior non-overlapping 7-day sum;
- 7 days is fixed before PnL to aggregate weekly fee seasonality; no alternate horizon is authorized;
- rebalance: daily at 00:00 UTC;
- portfolio: long higher score, short lower score, equal absolute weights;
- target/open gross cap: 0.75; dollar-neutral by construction;
- no threshold, sign flip, alternate window, subset, regime filter, cadence, gross or rescue search.

Training only: existing 2023/2024/2025 folds through 2025. Validation remains closed. Phase083/opened holdout and all future holdout data are forbidden for selection. V16/V99 excluded.

Frozen mandatory gates:
1. aggregate BASE return > 0;
2. aggregate BASE daily PF > 1.10;
3. aggregate BASE max drawdown >= -35%;
4. aggregate BASE worst day >= -12%;
5. every 2023/24/25 fold: return > 0 AND daily PF > 1.02;
6. severe and supersevere: return > 0 AND daily PF > 1.00;
7. largest absolute asset contribution share <= 60%;
8. top-10 absolute daily-return concentration <= 60%;
9. max open gross <= 0.750000001.

Report return/CAGR, tails, worst/best day, DD, PF, payoff, win rate, positive/negative days, turnover, max open gross, max close gross, folds, costs/funding stresses, regimes, concentration, asset contribution and hashes.

Any failed gate => **REJECT_NO_RESCUE**. PASS_TRAINING may authorize only a separately preregistered validation.
