# V98 Independent Phase1132 — signed closed-trade accounting preregistration

2026-10-23, before any Y historical PnL. Phase1130 authenticated source-only crossrunner is separate from economics. Y Phase1127 15/15 corrected synthetic survival and Phase1131 growth metric unit tests are structural evidence, not CAGR approval.

To calculate Profit Factor, payoff and win rate honestly, every actual execution must emit **per-asset signed units, fill price, notional and exact fee**; zero-notional operations are not trades. Preserve self-financing cash/units exactly. Maintain a FIFO trade book: realized closed-trade PnL equals directional price difference less allocated entry/exit fees plus attributed signed native funding; partial exits, reversals and stop-first basket liquidation are included. Remaining lots retain their unrecognized PnL, entry fees and funding. The independent invariant is **initial capital + realized PnL + unrealized PnL = hourly cash + marked units** at every hour, with 1e-6 USD tolerance in deterministic synthetic fixtures.

Two funding orderings are preregistered: `carried_before_fill` charges/credits carried t-1 units, and `new_after_fill` charges/credits the newly filled pre-stop units. On an intrabar stop, never book favorable credits whose timing cannot be guaranteed. Neither ordering may be selected after seeing outcomes; both must survive the complete 90-cell training matrix. This observer must not modify alpha, risk thresholds, fees, slippage, quote capacity, signs, windows, targets or positions.

Tests: signed long/short, FIFO partial exits, atomic reversals, fees, funding order, stop funding, 200-hour cash/NAV identity under both orders, no future data. No 2025/2026+, Phase083, XRP or external benchmarks.
