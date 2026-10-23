# V98 Independent Phase1202 — AD causal-risk full synthetic gate (2026-10-23)

Phase1198 90/90 benign and Phase1200 local 90/90 crisis used **fixed synthetic governor inputs**; this is not sufficient for official historical execution. Integrate Phase1201 strict t-1 rolling OHLC downside/upside, 336h minimum/prior quote and 720h adverse native funding risk inputs into the **same** Phase1198 stateful cash/inventory executor, without changing its sleeve architecture, fee schedules, funding timing or 81-corner governor.

The Phase1198 `one_cell` may gain an **optional risk-input argument**; default behavior must remain byte-for-byte semantically identical for prior synthetic evidence. New Phase1202 calls it with Phase1201 computed arrays at execution t. Run both benign and stress-activated crisis fixtures through all five paths x three capital modes x three fees x two funding timings: **180 synthetic cells**. Require every cell executable and actual-NAV stress activation in crisis AD_full. Preserve failures; no parameter/threshold/gross rescue if this gate fails.

All input windows must end t-1, no 2025, no XRP, no external benchmarks, no historical AD system PnL. Source and static hash gates remain separate. This phase is only structural readiness for full code freeze and subsequent official chronological economic evaluation.
