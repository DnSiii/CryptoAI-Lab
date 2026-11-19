# V98 C19 — preregistered architecture (training only)

Registered before any C19 replay. This is a distinct **persistent-trend / shock-continuation / relative carry / capitulation-recovery** seven-slot portfolio, not a parameter rescue of C18. No 2026+, XRP, Phase083 holdout, V14/V15/V99 information, or benchmark selection.

Universe: authenticated Clean-4 hourly BTC/ETH/BNB/SOL, Dec-2022 warmup to Dec-2025, native funding. Signals use completed closes only, next-open execution, gross <=0.90, per-asset <=0.40, no shorts, rebalance every 72h, warmup 2160h.

1. Growth Core (0.50 budget): 90-day positive return and close above 90-day geometric mean; score proportional to positive 90-day return / 30-day realized volatility.
2. Opportunity (0.20): 3-day return > 0 and 3-day high breakout over prior 30-day highs; equal-weight qualifying assets.
3. Relative Value (0.20): positive 30-day return above cross-sectional median and positive 7-day return; rank top two by 30-day excess over median, equal weight.
4. Stress/Recovery (0.10): 30-day drawdown below -20% followed by positive 3-day return and 7-day return exceeding prior 7-day return; equal-weight qualifiers.
5. Regime Router: breadth of 90-day positive returns: 0 assets => 0, 1 => 0.5, 2+ => 1.
6. Dynamic Allocator: allocate only to active sleeves, renormalize budgets across active sleeves, then use existing causal V98 composition and caps.
7. Risk Governor: existing V98 causal overlay, gross 0.90 and asset 0.40 caps; no leverage expansion.

Preregistered reject gates: audited ledger arithmetic, exact 27048 hours, source hashes, causal t-1, 1x/2x/4x cost stress, 2024 and 2025 each strictly positive at 4x, no hidden shorts, concentration, yearly diagnostics. Success on training is **not validation**. If passing, freeze candidate and conduct chronological separately isolated validation and marginal ablations before any external benchmark; otherwise reject without sign/window/threshold/cost rescue. No promotion or paper/live operation without all gates.
