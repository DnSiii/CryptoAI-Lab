# V98 Independent GL — pre-result order-invariant conservative funding risk authorization (2026-10-26)

**Infrastructure preregistration before GL governor code and any GL economic PnL.** This is a future-engine physical risk fix, not a re-run, retune or rehabilitation of rejected GH/GI/GJ/GK. Their frozen decisions remain final. All changes GL namespaced.

## Verified motivating anomaly
[GJ frozen funding-boundary replay](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40294176578) shows **0 trades at funding-event hours** in each of six GJ full cells despite 105 fill hours. Therefore `carried_before_fill` versus `new_after_fill` must have identical actual signed funding cashflow on any identical portfolio path. Yet their final NAV and sleeve marginals diverged. Static inspection of the generic V98 `EpochRiskGovernor._authorize`, `govern_units`, and `CGBufferedGovernor.buffered_safe` shows the *authorization* uses the requested funding-order scenario as a separate collateral-reserve assumption even at hours with no funding event. This changes positions and then returns, confounding funding-order sensitivity with strategy exposure changes.

## Exact proposed physical fix
For future GL-only risk authorization, always call the existing CG buffered governor with the **conservative carried-before-fill** reserve, regardless of which funding ordering the physical settlement scenario later uses. Do not change native `settle_hour` or actual event timestamps. For any candidate position n and old position o, the generic reserve penalty is `max(0, payer_reserve-new_reserve)`. In the carried case `payer_reserve=R(old)`; in new-after case `payer_reserve=R(n)`, making the penalty 0. Thus carried authorization is always **at least as strict** as new-after authorization. This fixes spurious order-specific risk targets without relaxing risk, changing signals, inventing leverage, or touching frozen infrastructure.

## Locked checks before any economic GL candidate
1. Exact same input risk state, targets, prior liquidity and fee mode -> GL authorization and ratchet outputs identical under both requested settlement orderings.
2. GL output equals original CG output with carried-before-fill on the same state; conservative CG buffered safety, staged 81-corner and no hidden borrowing unchanged.
3. Actual settlement remains separately parameterized by both orderings; no false equality asserted if trades occur at funding-event hours or prior cash histories differ.
4. No 2025 holdout, 2026+, XRP, Phase083, external benchmark, Frozen or paper read. Only authenticated Clean-4 2023-2024 can be used by any later preregistered complete GL engine. No live trading.

This is a mechanical causality/reproducibility correction, not evidence of profitability. A future GL complete seven-slot candidate needs separate preregistration and all 30-cell/independent-oracle/economic gates; rejected predecessors cannot be rescued.
