# V98 Independent — Clean-4 native carry and price regime diagnosis (2026-10-24)

**Training-only, no strategy PnL and no candidate selection.** Source: original PINNED `aj1259-official-source-ubuntu-24.04` artifact ID `12529621974` from run `40018746960`, using exactly four 18,288-hour CSVs (2022-12-01 through 2024-12-31), `phase1000_four_asset_conservative_bounds_source_only.csv` (9,144 native funding events) and the official receipt. No 2025/2026+, XRP, Phase083, V14/V15/V99. This is a descriptive causal-design diagnostic, NOT a backtest, not an optimization grid, and not proof of future performance.

| Asset | 2023 spot-like close return | 2024 spot-like close return | 2023 sum native 8h funding rates | 2024 sum native 8h funding rates |
| --- | ---: | ---: | ---: | ---: |
| BTCUSDT | +156.03% | +120.10% | +0.07866 | +0.11957 |
| ETHUSDT | +91.29% | +45.23% | +0.08260 | +0.12997 |
| BNBUSDT | +26.77% | +123.91% | −0.08345 | −0.03332 |
| SOLUSDT | +919.92% | +85.44% | +0.01297 | +0.13657 |

**Interpretation:** positive native funding is paid by a long and received by a short at the actual event; negative funding is received by a long. These **unweighted funding-rate sums are not funding PnL** and cannot be added directly to portfolio CAGR: realized notional, conservative mark, exposure timing, order sequencing, fees and slippage matter. BNB's negative annual funding both years suggests a potential causal carry asymmetry, but 2023 BNB price appreciation lagged BTC materially; selecting the lowest-funding asset without a separate trend/relative-return test may lose more price PnL than carry earns. The four-asset mean pairwise hourly log-return correlation was ~0.690 (2023) and ~0.733 (2024), so cross-asset longs share systemic beta and are not independent crash hedges.

**Reproducibility warning:** the exact source artifacts are currently set to expire on **2026-11-22** (per GitHub Actions artifact metadata). A durable, immutable V98-only copy or a verified archive-rebuild workflow is needed before expiry to preserve long-run rerunability; this does NOT currently block training because the pinned artifacts are available. Do not change Frozen or V99 sources/workflows.

**Research implication:** a genuinely new complete seven-slot engine could evaluate a *preregistered causal trend-confirmed funding-receiver allocation* and a stress overlay that receives, rather than pays, native funding when feasible. This is a hypothesis only; do not use these descriptive annual returns to cherry-pick fixed winners or rescue rejected sleeves. Require full 90-cell economic gates, independent future validation and reproducibility before any promotion.
