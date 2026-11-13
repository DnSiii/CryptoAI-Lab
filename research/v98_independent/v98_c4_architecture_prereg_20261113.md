# V98 C4 seven-slot architecture — preregistered 2026-11-13

STATUS: untested hypothesis; C3 rejected, no rescue or retuning. Independent Clean-4 only (BTC/ETH/BNB/SOL USD-M hourly Dec-2022 warmup–Dec-2025), native funding, no XRP, no 2026+, no Phase083. V14/V15/V99 prohibited for tuning.

**Distinct mechanism:** persistent multi-asset breadth and volatility-scaled trend participation, with countercyclical recovery and cross-sectional dispersion. Unlike C3, no highest-high breakout, no 56-day ranking, no 168-hour rebalancing. Use fixed 24-hour decisions, completed closes only, next-open execution. One fixed hypothesis, no grid.

Seven slots (unallocated budget stays cash):
1. Growth Core: 0.45 budget, equal among assets with positive 90-day and 30-day log return, and 30-day return greater than 2 times trailing 30-day hourly log-return standard deviation times sqrt(720). At most four names.
2. Opportunity: 0.10 budget, one asset with highest positive 7-day return if the equal-weight 30-day market return is positive and its 7-day return exceeds its own 30-day return / 4.
3. Relative Value: 0.10 budget, equal long exposure to assets with positive 30-day return exceeding equal-weight cross-sectional 30-day mean, provided market 30-day mean is positive. No short.
4. Stress/Recovery: 0.10 budget, equally among assets whose 7-day return turns positive while 30-day return is negative, only if at least two assets have negative 30-day return.
5. Regime Router: existing causal V98 regime_multiplier unchanged.
6. Dynamic Allocator: existing V98 compose_weights unchanged.
7. Risk Governor: existing V98 governor_multiplier unchanged.

All windows exact completed hourly closes: 2160, 720, 168; sample stdev over 720 one-hour log returns. Deterministic asset-order tie break. Recompute every 24 hours. No leverage, no additional parameter fitting.

**Evaluation and decision before any promotion:** authenticated full 27,048-hour replay with 1x/2x/4x native costs/funding; exact accounting, source SHA, t-1 prefix invariance, chronological 2023/24/25 and monthly performance, concentration, tails, DD, PF, payoff, positive days, regime sensitivity, four leave-one-out marginal contributions with no redistribution. If 2025/4x remain economically weak, or any material sleeve has robust negative marginal contribution, reject complete C4 rather than tune it. No holdout access before internal freeze and separate validation. External benchmarks only afterward.