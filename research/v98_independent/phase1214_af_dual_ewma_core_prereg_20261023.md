# V98 Independent Phase1214 — AF long-only dual-EWMA Growth Core prereg (2026-10-23)

AF first independent executable component, before any AF historical system PnL. Clean-4 continuous UTC hourly OHLC, quote, native signed funding/event, Dec-2022 start and **end strictly before 2025**. No AD/AE strategy source imports, XRP, 2026+, external benchmarks or historical PnL.

At completed close t, update fast and slow EWMAs of each asset's completed log close return (span 36h and 288h, alpha=2/(span+1)); t's decision may first trade at **t+1 open**. Zero intents before 288 completed bars. Score per asset = max(0, 0.70*EWMA36 + 0.30*EWMA288 - 0.00015 hourly friction hurdle). Require >=2 assets with positive fast and slow growth persistence and strictly prior 336h quote minimum >0 for entry (full 336h warmup for liquidity). If not, remain cash; this is an entry filter, not an objective of cash maximization.

Normalize positive scores into a **long-only 0.75 total growth participation budget**, with max 0.30 per asset, using deterministic capped redistribution. If fewer than three positive assets, unused capacity remains cash; no leverage or short. This budget is source intent only, not a realized executable portfolio. Relative Value, Opportunity, Stress, Router, Dynamic Allocator and Governor must later compose and constrain it without post-result rescue.

Gate: exact t+1 causality, no future-bar leakage, no short, no hidden leverage, finite outputs, deterministic digest and positive activation on a preregistered synthetic uptrend. No performance claims from synthetic source tests.
