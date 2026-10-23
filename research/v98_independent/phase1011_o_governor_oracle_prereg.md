# V98 Independent Phase1011 — O governor independent synthetic 16-corner oracle

Preregistered source-only robustness test, before any O historical economic PnL and without changing frozen O target code or the quarantined Phase1008 pins. Prior N was rejected on all 90 intrabar cells; O must independently prove its *mathematical* ex-ante governor is correct before economic training. Synthetic success is never historical profitability.

Generate 3,000 deterministic seeded Clean-4 long-only target vectors with nonnegative weights, per-asset <=70%, gross <=150%, and 720h-style plausible independent upside/downside shocks in [0, 80%]. For each vector, evaluate O's unchanged `robust_scale`, then an independent 16-corner direct-equity bisection oracle over k in [0,1] (36 iterations), checking gross<=175%, asset<=70%, and worst-case stressed equity>=10%. Require every O scaled target to survive all corners and `abs(k_O-k_oracle)<=1e-8`; reject on false acceptance or excess de-risking. Include nonfinite, invalid shock and warmup fail-closed witnesses, and a separate extreme 99% down/10x up scenario. Do not tune parameters, thresholds, returns or signs from results. No OHLC source acquisition, PnL, 2025+, holdout, XRP or external benchmarks.

Any failed test blocks O economic execution and triggers source-only bug diagnosis without touching frozen target logic or repinning.
