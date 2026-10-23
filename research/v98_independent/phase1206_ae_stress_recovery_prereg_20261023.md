# V98 Independent Phase1206 — AE prior-NAV convex stress/recovery preregistration (2026-10-23)

Independent source-only AE Stress/Recovery slot. Inputs at completed hour t: **actual** settled cash-plus-inventory NAV at close t, and equally weighted Clean-4 market return close[t]/close[t-1]-1 (or log return) at completed t. The returned target is eligible **only for next open t+1**, never a same-bar protective fill. The executor must later charge realistic fees, funding, slippage and liquidity for every hedge entry/exit.

Track running high-water NAV peak. Enter stress if prior/current completed NAV drawdown <= -12% or completed market log return <= -3%. Stress target is equal-weight Clean-4 short hedge with total gross 0.24 (each -0.06); it is **not** assumed to have been held before the triggering bar. Maintain hedge until 48 consecutive completed hours of NAV drawdown > -5% and nonnegative market log return; then exit target to zero for next open. A fresh shock resets the recovery counter. No hidden leverage, same-bar stop, same-bar hindsight or threshold tuning after seeing results.

Structural gate: deterministic 48h recovery, actual NAV rather than virtual NAV, strictly sequential state, nonfinite/insolvent fail-closed, no PnL/2025/external benchmarks. Passing source-only tests is not evidence of economic performance or survival. Full seven-slot gate remains mandatory.
