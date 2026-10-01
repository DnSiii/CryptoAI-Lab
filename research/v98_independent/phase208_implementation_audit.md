# V98 Independent — Phase208 pre-result implementation audit

Status: **completed before economic output inspection**.

## Frozen-spec conformance
- Branch and namespace restricted to `research/v98-independent-zero` and V98 Independent files.
- Closed grid remains exactly 8 specs: W {24,72} × Q {0.10,0.25} × H {8,24}.
- Scoring folds remain calendar 2023, 2024, 2025 with only causal warm-up before each fold.
- Validation/final holdout is not read.

## Causality audit
At decision hour `t`, realized-volatility uses returns ending at `t-1`; the percentile reference window is additionally lagged so the current RV observation is excluded. Breakout comparison uses the `t-1` close against the high/low of the 24 completed bars ending at `t-2`. Thus no high/low/close from decision bar `t` enters the signal.

## Execution-interval audit and correction
Before any Phase208 economic result existed, review found that label-inclusive assignment plus close-to-close returns could make the intended H-hour holding interval ambiguous. The evaluator was corrected pre-result to:
1. assign position rows with positional half-open interval `[i, i+H)`;
2. calculate realized price PnL on open-to-open returns;
3. charge entry turnover at `t` and exit turnover at `t+H`;
4. include funding while the position is active.

This is an integrity correction only; it does not alter the preregistered signal, grid, thresholds, folds, costs, or selection rule. It implements the preregistered instruction "enter at t open" and "hold exactly H hours" literally.

## Required diagnostics
Evaluator emits return, max drawdown, Profit Factor, payoff, win rate, positive-day fraction, trade count, best/worst full trade, p01/p05/p50/p95/p99 full-trade PnL, asset contribution/concentration, and causal BTC bull/bear/sideways decomposition for every spec/fold/cost combination.

## Reproducibility and firewall
Workflow rebuilds canonical training prices, asserts monotonic/unique timestamps and strict `<2026-01-01` for prices and realized funding, executes the evaluator twice, requires identical file SHA256, and applies the mechanical three-fold base-cost coherence gate. No rescue filter or post-result parameter expansion is permitted.
