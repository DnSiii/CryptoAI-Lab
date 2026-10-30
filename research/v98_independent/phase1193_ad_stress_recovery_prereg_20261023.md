# V98 Independent Phase1193 — AD stateful drawdown insurance sleeve preregistration (2026-10-23)

AD Stress/Recovery is a **conditional, stateful insurance demand**, not a free stop order or an objective to minimize volatility. Actual cash-funded inventory, funding, 81-corner survival, exit capacity and costs remain mandatory in the future complete AD executor. No historical AD system PnL is computed by this module.

At completed hour t, consume the **actual realized AD portfolio NAV through t** (not a hypothetical future NAV) and Clean-4 close prices through t. Compute drawdown = NAV_t / max(NAV_0..NAV_t) - 1. Compute equally weighted market 12h log return r12_t and previous non-overlapping 12h return r12_{t-12}; downside acceleration a_t=r12_t-r12_{t-12}.

- Trigger hedge only if drawdown <= -12% and acceleration <= -4 percentage points (log). Demand **short** 15% gross equally across Clean-4; if drawdown <= -20%, demand short 30% gross. These are sleeve *targets* for a cash-funded, self-financing governor, not guaranteed executable fills.
- Maintain hedge at least 24 hours; escalate from 15% to 30% if drawdown deepens, **never de-escalate until recovery**. Unwind demand only after minimum dwell AND drawdown >= -6% AND acceleration >= +1 percentage point (log). The executor must actually fill unwind orders under capacity or fail closed.
- No upside target ceiling, no retrospective sign flip, no AC uniform short-on-breadth rule, no free stop or ex-post risk minimization. Prior realized NAV cannot include the trade this signal is about to initiate.
- Source chronology starts 2022-12-01, 336-hour warmup, no 2025+, XRP, external benchmarks or contaminated Phase083. Fail on nonpositive/nonfinite NAV, invalid OHLC or future access.
- Synthetic tests: activation, escalation, min dwell, recovery, no instant execution, prefix causality, no PnL computed here. Actual AD allocator must prove positive marginal log wealth of the stress sleeve on frozen complete AD, rather than assume standalone hedge profitability.
