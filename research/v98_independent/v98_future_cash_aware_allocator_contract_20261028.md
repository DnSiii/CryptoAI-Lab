# V98 Independent — next-architecture cash-aware allocator contract (2026-10-28)

**Prospective infrastructure contract for a future economically distinct composed engine, NOT a KN/KM rescue.** KN is permanently rejected. This contract is written before implementing the new allocator and before any new-architecture historical PnL. It does not revise KN's historical source, budgets, decisions or risk outcomes.

## Observed failure and hypothesis

KN original 30-cell receipts show the full book exceeded actual gross/NAV 1 despite nominal source budgets totalling 0.94. Different sleeves open at different historical NAVs while existing unit inventories appreciate; summing stale fixed units and new NAV-based requests can exceed currently available collateral. Merely having ex-ante weights sum to <1 does not prevent this. A future composed engine must allocate each **new incremental unit request** against *currently occupied physical AND pending requested gross*, using completed-close prices and settled NAV only. Rejected KN cannot be rerun with this new allocator.

## Fixed authorization rule

At source-close t, before a new row is requested, compute per-asset occupied units = max(current physically settled long units, sum of previously authorized long-only component units). This conservative max does **not** assume unfilled exits free collateral. Occupied gross = sum(occupied units * completed close). Reserve 5% of settled NAV for fees, funding, gap and funding-order uncertainty; target new-entry gross ceiling = 95% of NAV. For a row update, compute positive increments above that row's already authorized units; only those positive increments consume new gross. Negative increments (exits) are always allowed but never counted as immediate free cash. If requested positive gross exceeds max(0, 0.95*NAV - occupied gross), scale **only positive incremental units** proportionally; if none remains, skip the new entry. No synthetic borrowed cash, hourly NAV rebalance or retroactive authorization. Existing rows persist in exact units until their scheduled event or a physical risk cut. Source t executes no earlier than open t+1.

The physical governor and 81-corner settlement remain independent; reject a future candidate on actual gross/NAV >1, severe cost, liquidation capacity, drawdown or tail violations. The 5% reserve is a survival constraint, not a limit on long-run CAGR; reinvestment is permitted at each genuinely scheduled event when collateral is available. No changes to existing fee/funding or participation models.

## Acceptance of infrastructure (not engine)

Deterministic tests must prove: no extra gross beyond available collateral on simultaneous entries; a second sleeve clipped to actual free NAV; no same-hour recycling of unfilled exits; no silent hourly re-entry; a row update on the same asset consumes only its positive increment; negative reductions always pass; nonfinite/negative/cash-invalid inputs fail closed. Only after these pass can a distinct complete seven-slot alpha architecture be preregistered, run on Clean-4 2023/24 and evaluated through 30 physical cells, independent oracle, chronological validation and untouched future holdout.

**No 2025/2026+, XRP, 1m, V14/V15/V99 internals, Frozen or paper access. No live orders.**
