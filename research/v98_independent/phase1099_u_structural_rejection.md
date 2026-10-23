# V98 Independent Phase1099 — U structural integration rejection (NO historical PnL)

2026-10-23. This is a **pre-economic synthetic structural failure**, not an official historical profitability result. U is NOT a valid frozen champion. Do not use 2025 or external benchmarks.

After publishing the exact U source, full-coverage stop oracle, event-time funding buffer, and synthetic remote CI (21/21 tests passed), an independent **end-to-end synthetic** composition probe joined all five U paths to the causal 336h protective-shock source and funded bracket ledger. A seeded 2,100h synthetic four-asset OHLC stream (Dec-2022 warmup, 2023 simulation), with native-style 8h synthetic funding events, 1% capacity and base costs, failed **all 5/5 paths** before completion:

- U_full: hour 18 after fold start, U_PATH_ASSET; target BNB weight 0.44998 against asset cap 0.45.
- U_minus_opportunity and U_minus_stress: same hour 18 U_PATH_ASSET.
- U_core_only: hour 74 U_PATH_ASSET, BTC target 0.44998.
- U_minus_relative_value: hour 74 U_UNSUPPORTED_PREPLACED_REVERSAL.

The risk is structural: U's point-in-time scaling saturates an asset at 0.44998, leaving essentially no margin for next-hour high/low variation, costs and funding; an OCO stop cannot guarantee intrabar compliance for favorable asset price moves. Signed reversals also lack dual preplaced linked protection. Do not cosmetically adjust U's .45 cap, sign, lookback, fee, leverage, or thresholds after these failures.

**Decision: U_full STRUCTURALLY REJECTED before economic PnL; NO historical CAGR, 90-cell evaluation, 2025 validation, or external comparison is authorized.** The four-runner U source-only authentication already launched may finish for provenance evidence, but cannot promote U. Preserve U artifacts as rejected. Next architecture must be genuinely distinct and portfolio-first, with ex-ante worst-corner feasible exposure rather than a point-in-time capped target.
