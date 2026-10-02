# V98 Independent Phase214 — preregistration

Status: **FROZEN BEFORE RESULTS**

## Hypothesis
A scientifically distinct OHLC family: **volatility-compression breakout continuation**. After an unusually compressed realized-range state, a causal breakout beyond the recent price envelope may have better continuation economics than unconditional close-location continuation. This tests state transition (compression -> expansion), not Phase212 reversal or Phase213 candle-location continuation.

## Data / firewall
Training-only canonical 1h futures OHLC for ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT; funding PIT. Hard cutoff `<2026-01-01`. BTC may be used only for the already-standard causal regime label, never to select/tune a spec. Validation/final holdout stays closed.

## Causality
At decision bar t, all state/envelope statistics end at t-1. Compression statistic is median true/high-low range fraction over the most recent compression window ending t-1 divided by its trailing historical median ending t-1. Breakout uses close(t-1) versus rolling high/low envelope ending t-2, so the breakout bar is not inside its own reference envelope. Position starts at t and holds fixed H hours. No contemporaneous/future feature.

## Frozen grid — exactly 8 specs
Cross product:
- compression window C: {12h, 24h}
- compression ratio threshold q: {0.70, 0.85}
- hold H: {3h, 6h}

Fixed, non-tuned constants:
- reference envelope: 48h ending t-2
- compression baseline: trailing 30 days (720h) ending t-1
- long if compressed and close(t-1) > prior 48h high; short if compressed and close(t-1) < prior 48h low; otherwise flat
- equal risk/notional treatment across eligible alts, no asset deletion

## Evaluation
Chronological folds: 2023, 2024, 2025. Report base/severe/supersevere realistic round-trip costs using existing V98 conventions plus realized PIT funding. For every fold/spec/cost: return, max drawdown, Profit Factor, payoff, win rate, positive days, trades, p01/p05/p50/p95/p99 and worst/best trade, asset returns/concentration, bull/bear/sideways regime metrics.

## Mechanical training gate
A spec is training-fold coherent only if base return > 0 AND base PF > 1 in each of 2023, 2024, 2025. This is necessary, not sufficient for promotion. Any coherent spec must next survive severe/supersevere, tails/concentration/regimes and reproducibility without changing the frozen definition. If 0/8 pass, close family as `REJECT_FAMILY_NO_RESCUE`.

## Reproducibility / anti-overfit
Evaluator output must be deterministic and byte-identical on two executions. No rescue by sign inversion, regime filtering, asset removal, parameter expansion, opened holdout, or V99-derived information. Any next family after rejection must be scientifically distinct and preregistered before results.
