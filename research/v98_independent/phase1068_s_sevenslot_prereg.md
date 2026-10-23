# V98 Independent Phase1068 — Architecture S preregistration (2026-10-23)

**New complete engine, not an R/Q repair.** No S economic results observed. Q and R frozen rejections remain final. Phase243 Clean-4 BTC/ETH/BNB/SOL USD-M 1h, Dec-2022 warmup, 2023/2024 chronological training, 2025 separate validation only after training success; no XRP, Phase083, 2026+, or V14/V15/V99.

## Hypothesis and north star
A **trend-persistence + volatility-release + cross-sectional relative-strength rotation + structured re-entry** portfolio can compound more strongly than either momentum/carry architecture under realistic signed execution. The objective is maximum long-run log wealth/CAGR subject to survivability, not minimum risk; upside ceiling undefined.

## Seven independently defined slots (fixed before data)
1. **Growth Core:** positive 24h/168h EMA slope alignment with 96h realized directional-efficiency confirmation; long-biased, quality-weighted cross-asset exposure. Not Q 72/504 momentum or R 48/336 log momentum.
2. **Opportunity Sleeve:** 12h range compression relative to prior 168h median followed by 4h directional range expansion and positive quote-volume acceleration; signed 8h event persistence. Not R 24h channel breakout.
3. **Relative-Value Sleeve:** cross-sectional 96h volatility-adjusted *relative trend-strength* rotation, centered to net-zero; no Q residual z-reversion and no R 72h funding carry. Native funding remains an execution cost, not this alpha's input.
4. **Stress/Recovery Sleeve:** re-entry after a 48h portfolio-wide drawdown and a two-step higher-low confirmation, with 24h cool-down; long-only recovery, not Q shock fade or R 6h downshock breadth.
5. **Regime Router:** 168h market trend, 72h cross-sectional dispersion, and realized-vol expansion, 24h hysteresis. Three causal states.
6. **Dynamic Allocator:** state-conditional opportunity/growth priority weighted by current causal signal confidence and funding-cost headroom, no past-return optimized shadow weights and no forced allocation to inactive sleeves.
7. **Risk Governor:** independent signed 16-corner margin/fee/funding/capacity governor, fixed per-asset .45, net .75, gross 1.35, equity floor .25; executable at t+1 using t-1 completed information. No hidden leverage.

## Non-negotiable source and freeze gates
- **Typed transport:** authenticated OHLC (18288,4); native funding rate/event (18288,4); conservative mark (18288,4); independently constructed vendor-attested **mark_low_high (18288,4,2)**. Explicit source checksum and event sign consistency. Any shape mismatch blocks **before PnL**.
- **Determinism:** quantize to six decimal places conservatively with post-serialization asset/net/gross checks; two independently provisioned CI runners must yield byte-identical five-path hashes before freeze. No post-result hash substitution.
- **Ablations:** S_core_only, S_full, S_minus_opportunity, S_minus_relative_value, S_minus_recovery. Fixed 5 x 3 fee tiers (0.0007,0.0012,0.0020) x 2 funding orders x 3 capital modes (10k/1m/10m) = 90 chronological cells.
- Require all 90 valid 2023/2024 folds and positive S_full log wealth in both years under base/severe costs and both funding orders/capital modes, with positive marginal vs all four ablations; monitor DD, tails/CVaR, PF, payoff, win rate, positive days, regime exposure, HHI, intrabar 16 corners and reproducibility. Any failure rejects S without rescue.
- Do not access V14/V15/V99 until S is internally frozen, passes chronological training and separately passes untouched 2025 validation.

## Execution order
(1) implement S seven-slot source and independent signed transport/oracle; (2) synthetic causal and adversarial tests; (3) two-run source attestation and deterministic hashes; (4) freeze; (5) official 90-cell economics; (6) reject or separate 2025 validation. No parameter grids, sign/window/threshold rescue, or holdout-driven selection.
