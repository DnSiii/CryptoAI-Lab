# V98 Independent — Phase069 preregistration

## Status
PRE-REGISTERED BEFORE PNL. Training only. Validation and final holdout remain closed.

## Independent hypothesis
Cross-sectional **idiosyncratic momentum**: rank assets by their trailing 20-day return after removing the contemporaneous equal-weight universe return over the same window. Long the asset with the highest residual return and short the asset with the lowest residual return. This asks whether asset-specific medium-horizon continuation exists after removing the common crypto beta component; it is distinct from Phase065 raw 30-day momentum, Phase067 realized-volatility spread, and Phase068 3-day reversal.

## Frozen universe and timing
- BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT.
- Training folds: calendar 2023, 2024, 2025 only.
- Lookback: exactly 20 completed UTC daily bars.
- Signal for day t uses information available through t-1 only.
- For each asset i: residual_mom_i = R20_i - mean_j(R20_j), where R20 is trailing close-to-close 20-day return ending t-1.
- Long highest residual_mom; short lowest residual_mom.
- Rebalance daily at 00:00 UTC using the existing V98 causal execution convention.
- Equal absolute long/short legs; target gross exposure 0.75; market-neutral target net 0.
- No thresholds, volatility filters, regime filters, asset exclusions, or parameter search.

## Costs and funding
Use the same V98 Independent realistic execution/funding accounting already frozen in the research harness. Evaluate BASE, severe, and supersevere cost schedules. No post-result cost adjustment.

## Required diagnostics
Aggregate and each chronological fold: total return/CAGR, max drawdown, daily Profit Factor, payoff, win rate, positive/negative days, worst/best day, p01/p05/CVaR05, turnover, gross/net exposure and ruin flag. Also report severe/supersevere outcomes, regime decomposition, asset contribution/concentration, tail concentration/pathologies, causal/integrity tests, and reproducibility hashes.

## Training promotion gate
All must hold under BASE unless explicitly stress-qualified:
1. Aggregate total return > 0 and daily PF > 1.05.
2. Each of 2023, 2024, 2025 has total return > 0 and daily PF > 1.00.
3. Aggregate max drawdown > -35%.
4. Severe total return > 0 and PF > 1.00.
5. Supersevere must not indicate ruin and must not erase more than 90% of BASE terminal profit.
6. No single asset or small tail cluster may explain the result to a degree judged pathological by the frozen diagnostics.
7. Causality/integrity/reproducibility checks must pass.

Failure of any hard gate => REJECT_NO_RESCUE. Do not tune Phase069 using its result. PASS => freeze candidate before opening a separately defined validation period. Final holdout remains untouched until a formally frozen candidate reaches that gate.

## Isolation
Only V98 Independent namespaced files on research/v98-independent-zero may be used or changed. Never inspect or use V99 to select/tune this hypothesis. V16 Frozen and all V99 state are immutable/out of scope.
