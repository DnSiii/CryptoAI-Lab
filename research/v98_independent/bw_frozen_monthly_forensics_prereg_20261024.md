# V98 BW frozen post-rejection forensic protocol — 2026-10-24 08:44 BRT

Scope: **diagnostic only** on already rejected BW, without changes to BW source, weights, thresholds, governors, decision gates, historical rejection, or model selection. This is NOT a new candidate and cannot rescue BW.

Data: same pinned Dec-2022–Dec-2024 Clean-4 original-byte training source from Actions run 40064588623. No 2025, no 2026+, no XRP, no V14/V15/V99.

Cases preregistered before diagnostic results: BW_full, BW_core_only, BW_minus_opportunity, BW_minus_RV, BW_minus_stress; immediate US$10k; base and severe native fees/slippage; carried-before-fill funding ordering. Ten immutable cases.

For each of 16,272 executed hours, recompute per-asset native funding, open gap PnL, open-close PnL, fees, slippage and notional turnover using original units/market arrays. Aggregate by calendar month and asset. Reconcile each case with the existing immutable BW historical receipt to 1e-6 absolute / 1e-9 relative on funding, friction, turnover and final NAV. Independently reconcile hourly PnL cashflows and monthly to annual NAV deltas. Preserve original 81-corner replay evidence from run 40090466805; this forensic does not replace that independent audit.

Analysis decision: diagnostic attribution only. Identify months and assets behind negative ablation marginal log growth. No parameter search, no trading promotion, no holdout access, no return claims beyond original historical training.