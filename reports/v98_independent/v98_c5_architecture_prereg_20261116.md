# V98 Independent C5 — pre-registered composed architecture (2026-11-16)

Status: HYPOTHESIS ONLY. No replay, no promotion. C4 remains rejected. This document fixes the design before seeing any C5 outcomes.

## Data, causal contract and separation
Use exclusively authenticated Binance USD-M 1h BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT Clean-4, December 2022 warmup through December 2025, with native funding and next-open execution from the V98 B0 executor. No XRP, no 2026+, no contaminated Phase083 holdout, no V14/V15/V99 consultation. At decision time t only closed candles through t-1 are available; all weights are executed at next open. Maintain 40% asset and 75% gross post-fill exposure gates. No parameter tuning on evaluation results.

## Seven slots — fixed first candidate C5
1. **Growth Core (45% maximum nominal)**: long-only trend participation via 90-day closing-price channel breakout (latest close above prior 90-day closing maximum), filtered by positive 30-day log return. Allocate equally to qualifying Clean-4 assets. Zero otherwise.
2. **Opportunity Sleeve (10%)**: select the single asset with the highest positive 7-day log return among those with positive 30-day return AND current 7-day realized volatility greater than its previous 30-day hourly volatility; activate only when the equal-weight market 30-day return is positive. Otherwise zero.
3. **Relative-Value Sleeve (10%)**: market-neutral cross-sectional pair: long the strongest 30-day log return asset and short the weakest, but only when the 30-day spread exceeds two times the cross-sectional standard deviation of 30-day returns. Each side nominal 5%. Funding and costs apply to both legs. Otherwise zero.
4. **Stress/Recovery Sleeve (10%)**: *distinct from C4 negative-30-day/positive-7-day recovery*: after a broad market drawdown of at least 12% from its trailing 30-day closing high, allocate 10% long to the asset with the strongest positive 48-hour return only if the equal-weight market 48-hour return is positive and its 48-hour closing price is above its preceding 48-hour maximum. Otherwise zero. The stress sleeve must add positive marginal terminal wealth at all 1x/2x/4x costs; downside reduction alone is not a pass.
5. **Regime Router**: market-wide 30-day positive return enables the Growth/Opportunity sleeves; the relative-value spread trade remains available in both market regimes; Stress/Recovery is enabled only in the specified drawdown/rebound state.
6. **Dynamic Allocator**: additive raw sleeve weights with no leverage or hidden normalization. Each sleeve stays within its nominal budget, with inactive sleeve budget held as cash. No retrospective sleeve reweighting.
7. **Risk Governor**: use the existing independent V98 next-open execution, native funding and friction, per-asset 40% and total gross 75% post-fill gates, rejecting any violation.

## Gates and decision rules
- No optimization grid or sign flip. One fixed C5 hypothesis. The full 27,048-hour Clean-4 replay must finish for all three cost levels (1x/2x/4x) and pass source hashes, causal checks, exposure checks, final-mark reconciliation and finite-value checks.
- Run leave-one-sleeve-out ablations for Growth, Opportunity, Relative Value, Stress/Recovery at all three costs, using identical execution mechanics. Require positive terminal-equity marginal contribution of **every** sleeve at each cost level; otherwise reject C5 with no rescue.
- Publish max drawdown, CAGR based on actual elapsed time, trade-level Profit Factor if derivable (otherwise explicitly unavailable), payoff, win rate, positive days, turnover, funding, tail losses, concentration and regime-specific performance. Distinguish index-grouped day approximations from calendar-day statistics.
- Establish chronological training/development and **separate** validation before any candidate is frozen. Use the pre-2026 eligible universe and do not let validation performance select or retune parameters. If a legitimate untouched validation window cannot be established, fail closed rather than using the contaminated Phase083 holdout.
- Only after a complete internally frozen and independently validated V98 candidate may external benchmark V14/V15/V99 results be opened.

Economic objective: maximize long-run compounded wealth subject to survival, causality and reproducibility constraints. The 45/10/10/10 nominal budgets are hypothesis constants, not an upper ceiling on future V98 research. Rejection of C5 does not authorize changing its constants retroactively.
