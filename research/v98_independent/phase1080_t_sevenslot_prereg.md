# V98 Independent Phase1080 — T seven-slot low-turnover state-machine preregistration

2026-10-23. **Pre-economic**, independent new architecture; no S rescue or V14/V15/V99 access. Clean-4 BTCUSDT ETHUSDT BNBUSDT SOLUSDT Binance USD-M 1h, Dec-2022 warmup, chronological 2023/2024 training, 2025 separate validation only after training PASS. Exclude XRP, contaminated Phase083 and 2026+ data.

## Growth objective and new architecture
A persistent **low-turnover state machine** can capture multi-week compounding trends while avoiding hourly churn, exploit episodic funding dislocations, hold relative carry-adjusted leadership, and adapt to stress/recovery. Objective maximum long-run compounded wealth/CAGR subject to survival, realistic costs/funding, drawdown, tails, concentration, causality and reproducibility. No upside cap or hidden leverage; do not optimize minimum risk.

## Seven slots, parameters fixed before historical economics
1. **Growth Core:** long-only 720h and 168h positive log-trend agreement, 336h inverse realized-vol weights, 72h persistence. Not S 24h/168h EMA efficiency.
2. **Opportunity Sleeve:** negative funding dislocation (72h average below 1440h historical 10th percentile, minimum 720 observations), positive 48h price stabilization; 48h long hold, 96h cooldown. Not S compression/breakout.
3. **Relative Value:** 336h cross-asset carry-adjusted score = 336h log return minus 40 times 72h mean funding. Top/bottom pair +0.5/-0.5 only if spread >0.05, daily rebalance. Not continuous four-asset S relative momentum.
4. **Stress/Recovery:** broad market negative 168h trend with 168h realized vol above 1.2 × prior 720h median triggers short inventory in two highest-vol assets; positive 48h market reversal switches to long basket. 72h inventory persistence. Not S higher-low recovery.
5. **Regime Router:** 720h market trend, 168h realized vol vs lagged 720h median; defensive if trend negative and vol >1.20× baseline, expansion if positive and vol <1.10×; otherwise neutral. 72h hysteresis.
6. **Dynamic Allocator:** state budgets growth/opportunity/relative-value/stress = defensive [.15,.05,.25,.55], neutral [.55,.10,.25,.10], expansion [.65,.15,.15,.05]; active sleeves only, scaled by causal 72h native funding headroom, daily 00 UTC target latch. No return-optimized shadow weights.
7. **Risk Governor:** signed 16-corner cash/funding/fee stress, per-asset 0.45, net 0.75, gross 1.35, equity floor 0.25, capacity participation 1% of prior quote volume; 6-decimal canonical weights, post-serialization checks, execute t+1 using completed t information. No hidden leverage.

## Preregistered falsification gates
Paths: T_core_only, T_full, T_minus_opportunity, T_minus_relative_value, T_minus_stress. Synthetic causal and adversarial tests, repeated independent runner source recompositions with byte-identical hashes, signed marks and funding, then immutable freeze **before** historical PnL. 5 paths × 3 fee tiers (.0007,.0012,.002) × 2 funding orders × 3 capital modes ($10k/$1m/$10m) = 90 training cells, each with 2023 and 2024 chronological folds. All 90 must survive; T_full log wealth positive in both years under base and severe tiers across orders/capital modes; positive robust marginal against all four ablations. Report CAGR, DD, tails/CVaR, PF, payoff, win rate, positive days, turnover, funding, regime, concentration, capacity and determinism. Any failure rejects T without post-result rescue. No 2025 validation before training PASS; no external benchmark before 2025 PASS.
