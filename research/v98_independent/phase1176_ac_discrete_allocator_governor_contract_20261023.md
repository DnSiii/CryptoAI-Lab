# V98 Independent Phase1176 — AC executable allocator/governor contract (pre-implementation lock)

Date 2026-10-23. Complements AC Phase1173, before authenticated source comparison or historical AC system PnL. This is **not** a rescue of rejected AB/AA/Z/Y.

## Signed inventory and growth objective
- All decisions use prior completed hour t; proposed trades fill at t+1 open, never at t close. Maintain cash, four signed asset units and actual NAV. Mark-to-market every hour. Never manufacture reduce-only fills.
- AC intent integer s in [-4,+4] maps to a fixed 24h expected *log-return* proxy `mu = 0.003 * s` (a preregistered structural surrogate, **not** an estimated alpha or observed performance). Estimate 24h covariance only from prior 336 completed 1h log returns with a causal rolling window; use conservative PSD ridge 1e-8. Fixed horizon 24h, no grid.
- Choose discrete trades by deterministic per-asset finite candidates `{-1,0,+1}` at precommitted step notional `min(0.1% prior quote volume, 5% prior NAV)` (converted to units at prior close). At most four coordinate passes in asset order. Candidate objective: `log(1 + w·mu - 0.5 w'Cov24 w - estimated_fees - adverse_funding)` if argument > 0, otherwise reject. All costs and financing are net; no gross rescue or return cap.
- Actual quote execution cap per asset 0.4% prior-hour quote volume, plus 0.2% trailing 336h minimum quote volume on new/increased inventory. Entries must reserve **two full exits** under 0.4% stressed quote capacity; no phantom liquidity.
- Fees fixed base 0.0007, severe 0.0012, supersevere 0.002 per traded notional; slippage 0.002 each fill; governor always uses supersevere fee. Funding bound is the greater of native signed event stress and causal 720h absolute funding shock; no rebates in risk gate.
- Hard 81-corner stress uses signed low/mid/high price shocks per asset and self-financing cash. Max per-asset exposure 40% of stressed NAV; gross 120%; |net| 60%; stressed equity >=30% of prior NAV. Any infeasible carried inventory that cannot be reduced within available quote capacity fails closed.
- Opening gap against prior stop envelope cancels entry and checks actual carried inventory before any execution. An emergency reduction may occur only if it fits precommitted order capacity; otherwise report an explicit failure. Funding cash is applied to actually carried/new units according to both preregistered timing orders, with signed mark bounds.
- Freeze synthetic ledger before authenticated economic training; no tuning based on failures, historical PnL or 2025.

## Acceptance
Test exact self-financing, fee/funding debit, positive/negative units, 81 corners, low-volume infeasibility, t-1 causality, gap failure, deterministic allocation, severe/supersevere costs, concentration, and reproducibility on synthetic data. This implementation contract does **not** imply AC is economically validated. Only a full frozen 90/90 training gate can advance AC.
