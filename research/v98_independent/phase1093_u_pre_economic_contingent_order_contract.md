# V98 Independent Phase1093 — U pre-economic contingent-order mechanics and structural audit

**Date:** 2026-10-23. This is a preregistration *before U historical PnL* and does not revise any frozen T/S/Q/R source or result. U's seven-slot hypothesis was registered in Phase1090. No 2025+, XRP, Phase083, V14/V15/V99 or historical U economic returns were consulted.

## Exact contingent-order rules, to be frozen before historical training

- At close **t-1**, compute trailing **past-only** intrabar maximum down/up shocks and prior quote-volume capacity. A position's stop-market order is **reduce-only for 100% of the then committed quantity** at prior close × (1 - prior down shock) for long or prior close × (1 + prior up shock) for short. Zero or invalid source fails closed.
- Preplace a **reduce-only 1/3 take-profit limit** at prior close × (1 + prior up shock) for long or prior close × (1 - prior down shock) for short. Both orders are OCO. The limit only partially reduces exposure, preserving the possibility of uncapped further portfolio growth via subsequent decisions.
- If the same hourly bar touches both prices, assume the **adverse stop happens first**; never claim a favorable limit fill. If the bar opens beyond a stop, execute at the **worse opening price**, not the unreachable stop. Include adverse slippage at least equal to the scenario's fee tier and charge explicit fees.
- No position increase or sign flip is allowed through these contingent orders. Cap executable quantity by **1% of prior quote volume** per asset; any mandatory stop exceeding capacity rejects the cell, rather than assuming an impossible fill. Brackets for newly opened t positions must be linked to t-1 entry instructions; unprotected new positions fail the integrated gate.
- Verify pre-fill, gap, stop, and post-fill **all 16 signed high/low corners**, including funding debit, net/gross/asset limits, equity floor, and possible intrabar path ordering. A bracket fill alone is **not** proof of intrabar survival.

## Router and stress hysteresis interpretation

Phase1090 specifies 48h router and 72h stress hysteresis. Interpret both as **minimum state dwell after a change**, not a requirement for 48/72 *consecutive* triggering hours. In 30 seeded synthetic 2,100-hour universes, requiring consecutive stress evidence made stress **inactive in all 30**; minimum dwell activated stress in **643–906 hours**, with all four U_full ablations distinguishable in **30/30** seeds. This is a **pre-economic structural correctness decision**, not a post-result parameter rescue or evidence of alpha.

## Local source-only evidence and deployment status

A locally prepared U target-source prototype and independent bracket/16-corner oracle passed **19/19 synthetic unit tests**, plus **500 adverse order mutations**, and **30/30 synthetic source composition checks**. The full code upload to GitHub was rejected by the tool's safety checks; therefore **these local implementations are not represented as remotely published, authenticated, frozen, or economically approved**. The official GitHub branch currently contains only this preregistration and the Phase1091 immutable T rejection. Do not dispatch any U historical PnL until code publication, remote CI, independent source attestation, executable preplaced-entry brackets, and freeze are complete.

**Decision:** T permanently rejected at 0/90; U is a preregistered, **unfrozen** structural prototype. Next: complete integrated bracket execution and synthetic 16-corner path oracle, then remote reproducibility and only then 90-cell 2023/2024 economics.
