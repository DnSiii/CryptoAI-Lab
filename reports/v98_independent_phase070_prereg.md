# V98 Independent — Phase070 preregistration

## Status
PRE-REGISTERED BEFORE PNL. Training only. Validation and final holdout remain closed.

## Independent hypothesis
Cross-sectional **funding carry**: persistent positive perpetual funding is a direct observable cost paid by longs to shorts, while negative funding is paid by shorts to longs. Rank the frozen universe by trailing realized funding using only funding events known through t-1; short the asset with the highest trailing cumulative funding and long the asset with the lowest trailing cumulative funding. This tests a carry mechanism directly distinct from price momentum/reversal, realized-volatility spread, and OI-value hypotheses.

## Frozen universe and timing
- BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT.
- Training folds: calendar 2023, 2024, 2025 only.
- Funding lookback: exactly 7 completed UTC days (168 hours).
- Signal for day t uses funding observations available through 23:00 UTC on t-1 only; no same-day funding observation may enter the rank.
- Score = trailing 168-hour sum of realized funding rates.
- Long the lowest score; short the highest score.
- Rebalance daily at 00:00 UTC using the existing V98 causal execution convention.
- Equal absolute long/short legs; target gross exposure 0.75; market-neutral target net 0.
- No thresholds, price filters, volatility filters, regime filters, asset exclusions, or parameter search.

## Costs and funding
Use the same V98 Independent realistic execution/funding accounting already frozen in the research harness. The backtest must debit/credit actual realized funding independently of the funding signal. Evaluate BASE, severe, and supersevere cost/funding schedules with no post-result adjustment.

## Required diagnostics
Aggregate and each chronological fold: total return/CAGR, max drawdown, daily Profit Factor, payoff, win rate, positive/negative days, worst/best day, p01/p05/CVaR05, turnover, gross/net exposure and ruin flag. Also report severe/supersevere outcomes, regime decomposition, asset contribution/concentration, tail concentration/pathologies, causal/integrity checks, and reproducibility hashes.

## Training promotion gate
All must hold under BASE unless explicitly stress-qualified:
1. Aggregate total return > 0 and daily PF > 1.05.
2. Each of 2023, 2024, 2025 has total return > 0 and daily PF > 1.00.
3. Aggregate max drawdown > -35%.
4. Severe total return > 0 and PF > 1.00.
5. Supersevere must not indicate ruin and must not erase more than 90% of BASE terminal profit.
6. No single asset or small tail cluster may explain the result to a degree judged pathological by the frozen diagnostics.
7. Causality/integrity/reproducibility checks must pass.

Failure of any hard gate => REJECT_NO_RESCUE. Do not tune Phase070 using its result. PASS => freeze candidate before opening a separately defined validation period. Final holdout remains untouched until a formally frozen candidate reaches that gate.

## Isolation
Only V98 Independent namespaced files on research/v98-independent-zero may be used or changed. Never inspect or use V99 to select/tune this hypothesis. V16 Frozen and all V99 state are immutable/out of scope.
