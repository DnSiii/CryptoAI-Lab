# V98 Independent Phase196 — FROZEN BEFORE EXECUTION

## Hypothesis

After an unusually large *idiosyncratic* realized-volatility expansion, cross-sectional residual price dislocations partially revert. This is scientifically distinct from Phase195 liquidity-adjusted trend: liquidity is not a ranking signal and the economic direction is post-shock relative reversion rather than trend persistence.

## Information firewall

Training research window only: 2023-01-01 through 2025-12-31, evaluated as chronological folds 2023 / 2024 / 2025. All signal inputs at decision time t must be computed from observations available no later than t-1. No validation or final-holdout observations may be read. V16 and V99 may not be used for signal design, parameter selection, ranking, rescue, or interpretation.

## Signal family

For each asset and hour, using trailing returns ending at t-1:
1. estimate rolling beta to the equal-weight crypto market over 168h;
2. compute residual hourly returns and residual displacement over D hours;
3. compute residual realized volatility over 24h and compare it with its own trailing 168h median, producing a causal volatility-expansion ratio;
4. an asset is shock-eligible only when its ratio exceeds fixed threshold S;
5. among eligible assets, rank residual displacement; short the most positively displaced and long the most negatively displaced, dollar-neutral, equal gross legs; otherwise stay flat.

No contemporaneous t return, future quantile, full-sample normalization, liquidity rank, or Phase195 winner information is permitted.

## Closed grid

Exactly 8 specifications before seeing results:
- displacement D: {6h, 24h}
- volatility shock threshold S: {1.5x, 2.0x}
- hold/rebalance H: {6h, 12h}

No additional cells or rescue variants after execution.

## Economics and diagnostics

Use the same canonical V98 Independent training-only price/funding data and the same frozen base, severe, and supersevere cost/funding conventions already used by the immediately preceding V98 experiments. Report for every cell: total return/CAGR, max drawdown, daily Profit Factor, payoff, win rate, positive/negative days, turnover, gross/net exposure, chronological fold metrics, bull/bear/sideways regime behavior, tail concentration/CVaR, position concentration, and activity.

## Gate

Promotion requires a genuinely positive economically meaningful base edge, acceptable MDD, positive/credible PF and payoff, no decisive chronological fold failure, adequate regime breadth, and survival under severe and supersevere assumptions. A strong single year or regime cannot rescue failure elsewhere. Reproducibility must be byte-identical on two independent deterministic executions.

If the frozen gate fails, decision is REJECT_FAMILY_NO_RESCUE. No inversion or post-hoc threshold/holding-period expansion is allowed.