# V98 Independent Phase1217 — AF prefunded cash stress/recovery sleeve prereg (2026-10-23)

AF slot 4 is **actual collateralized cash optionality**, not an AE/AD short hedge. Cash remains available for future high-growth participation, not the optimized objective. No same-bar stop, free fill, naked short, synthetic option payoff or future NAV. The future executor must pay real fees/slippage and respect actual liquidity when moving between cash and long assets.

At completed hour t, update peak of **actual** cash-plus-inventory close NAV. Enter stress if completed NAV drawdown <= -15% or completed equally weighted Clean-4 market log return <= -5%. Stress reserves **55%** of NAV as unencumbered cash for the *next* open t+1; normal reserve is **10%**. Stay in stress until **24 consecutive completed hours** of NAV drawdown > -8% and nonnegative market log return; then return to normal 10% reserve for next open. Any new shock resets recovery counter. If NAV nonpositive or inputs nonfinite, fail closed.

The sleeve outputs only the desired **cash reserve fraction**, never signed futures positions. Future AF allocator must scale long-only Growth/Opportunity/RV notional to <= 1-reserve while pursuing maximum causal net compounded growth. Test strict sequential state, recovery timer, no future leakage, no PnL claims. Complete seven-slot and severe-cost gates remain mandatory.
