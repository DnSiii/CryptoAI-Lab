# C27 — preregistration before any C27 result (2026-11-20)

**Scope:** Independent V98, authenticated Clean-4 hourly Binance USD-M, December 2022 warmup through December 2025 only. No 2026+ access, no XRP, no Phase083 holdout, no V14/V15/V99 internals. C23–C26 remain rejected; this is a new architecture, not a rescue.

**Hypothesis:** A complete seven-slot engine with a *two-clock* design can preserve long-horizon upside while avoiding intraperiod cap violations: strategic signals are updated on a weekly clock, but a causal hourly safety governor trims only positions whose drift has breached the cap. The governor is not an alpha source and may not increase exposure between strategic updates. This differs materially from C26's weekly buy-and-hold drift.

1. Growth Core: multi-month trend and breakout persistence on each Clean-4 asset.
2. Opportunity Sleeve: volatility contraction followed by upward breakout.
3. Relative-Value Sleeve: cross-sectional momentum ranking on Clean-4 only.
4. Stress/Recovery Sleeve: recovery after documented historical drawdown.
5. Regime Router: BTC-based market breadth and volatility regime, calculated from completed closes.
6. Dynamic Allocator: normalized, nonnegative sleeve weights, strategic refresh every 168 hours after warmup; unused sleeve budget remains cash.
7. Risk Governor: at **every next open**, first mark existing holdings and native funding; if any asset exceeds 40% of current equity or aggregate long exposure exceeds 90%, sell only the minimum necessary to return within both limits, charging the exact same 1x/2x/4x transaction cost. No buy orders between weekly strategic rebalance points. A safety trim is explicitly a permitted off-calendar transaction, and is labeled separately in the ledger.

**Causality:** Strategy decisions use only completed t-1 closes. A safety trim triggered by the open-t mark cannot claim execution at that same open-t price; to avoid lookahead, the safety decision is queued for the **next** open. The audit must distinguish the transient marked exposure at open-t from the queued post-fill exposure at open-(t+1), including gaps and funding. If the post-fill limits cannot be guaranteed under next-open gaps, do not mislabel the result as continuously capped: use a conservative pre-emptive buffer defined *before* running C27, or fail the cap gate. No synthetic same-open fills.

**Frozen protocol before results:** Choose one deterministic rule set and one pre-emptive buffer from an ex-ante stress bound, not by observing C27 PnL. Log hourly pre/post weights, signal timestamps, queued safety orders, order types, native funding, fees/slippage, and the final mark. Verify 27,048 bars and 27,047 ledger rows for each scenario. Run independent accounting and chronological training/validation, severe and supersevere costs, annual/regime/tail/concentration metrics, drawdown, PF, payoff, win rate, positive days, and deterministic replay. Any failed gate rejects C27 without parameter rescue. Holdout remains untouched; benchmark other engines only after internal freeze and separate validation.

**Decision now:** hypothesis registered; **not implemented, tested, validated, or promoted**. Do not infer a return or successful cap compliance from this document.
