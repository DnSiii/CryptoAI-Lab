# V98 Independent Phase1105 — V linked execution contract, pre-economic

2026-10-23. V source and governor remain unfrozen. This specifies V's independent linked-order execution before any historical PnL.

At close t-1, create a protective full-quantity reduce-only stop-market and 1/3 reduce-only take-profit limit for all carried and planned same-side inventory. Use V's prior 336 completed-bar down/up shocks and 1% prior quote-volume capacity. If carried inventory and new desired target have opposite signs, place a **market-to-flat** at next open; defer opposite entry to a later open after a new close-based instruction. Never cross through zero or open an unprotected opposite position within the same bar. Insufficient capacity to flatten fails closed.

At open t, adverse market slippage and fee apply; any stop already crossed by the opening gap has priority and fills at worse opening, never at unreachable stop. When stop and limit are both touched in an hourly bar, stop is first. No fill may exceed actual units, and a mandatory stop with insufficient 1% quote capacity rejects the cell. Model all signed pre/post mixed 16-corner states, fee and realized funding debit ex post; no 2025, no PnL, no benchmark access.

This is a structural oracle gate, not economic validation. Next build V independent signed funded ledger, authenticate and freeze all modules before any 90-cell training.
