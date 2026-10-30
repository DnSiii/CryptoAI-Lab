# V98 Independent Phase1210 — AE actual-open self-financing cash/inventory executor prereg (2026-10-23)

The independent AE seven-slot engine requires an actual cash/inventory ledger, not virtual sleeve returns. Pre-register this before code or historical PnL. Source-only synthetic tests; no 2025, 2026+, XRP or external benchmarks.

At hour t open: carried signed contracts and actual cash are valued at prior close and actual opening prices. Reject prior-close/open gap insolvency. Use Phase1208 cash-anchored governor with Phase1209 strict **t-1** risk inputs to select maximal feasible candidate. Execute signed delta at opening * (1+sign(delta)*0.0035) with actual per-notional fee **base 0.0007, severe 0.0012, supersevere 0.002**. Cash is debited for buys and credited for sells, including slippage and fees; no free hedge, stop or flatten.

At native 8h funding event, signed funding = -sum(units * funding_rate * conservative_native_mark). For positive payer units*rate, mark at native high; for receiver units*rate negative, native low. Both preregistered accounting orderings must be evaluated: `carried_before_fill` applies funding to old contracts before opening orders; `new_after_fill` applies funding to new contracts after opening orders. Validate native mark range and event mask; no fabricated non-event funding. If funding makes cash-plus-inventory equity nonpositive, reject.

After fill and funding, verify **actual** 81 OHLC intrabar corners using hour t's realized high/low solely as a **post-trade audit**, never to choose t's orders. Require actual equity floor 0.30 of opening equity and caps asset 0.30, gross 0.95, absolute net 0.60 at all corners. NAV at completed close = cash + signed contracts * closing; reconcile to within 1e-8 and reject insolvency. Persist turnover, fees, signed funding, worst actual corner equity and growth projection fraction. No hidden leverage or synthetic profitability promotion.

If a structural or historical gate fails, reject without modifying preregistered parameters. Full seven-slot 180-cell causal-risk stress and official chronological training remain future separate gates.
