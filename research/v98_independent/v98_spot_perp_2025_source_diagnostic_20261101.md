# V98 Independent — 2025 official spot/perpetual source feasibility, no PnL (2026-11-01)

**Source-only result: verified, not a trading candidate.** Official Binance SPOT 2025 1h Clean-4 archives: 48/48 ZIP objects and 48/48 provider SHA256 sidecars verified; **35,040/35,040 asset-hours** (8,760 per BTC/ETH/BNB/SOL), **zero missing UTC hours**. Canonical observed-only CSV SHA256 `069bec10906e476e19470b042d40ce3fa7d654228de9cff50bd53ad91ed74156`. Source run [41328347003](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41328347003); independent audit [41328441679](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41328441679) rechecked chronology, row geometry, provenance, SHA256, all 35,040 rows and **2/2 tamper cases rejected**. This is 2025 **exposed training**, never independent validation.

**Separate 2025 spot/perp timestamp join, source diagnostic only:** spot and SHA-pinned V98 2025 USD-M 1h perpetual source (official receipt SHA256 `7ce4ec7e2a6980838fa0179729b3cc6da8f131806b03e070590146d6d6ca046b`) aligned at all 8,760 timestamps per asset. Define raw basis at each closed bar as perpetual close / spot close - 1. This is a source distribution, **not** a signal, entry rule, backtest, trade or future return.

| Asset | Median raw basis | 99th percentile absolute basis | Maximum absolute basis |
|---|---:|---:|---:|
| BTCUSDT | -0.04425% | 0.06566% | 0.17475% |
| ETHUSDT | -0.04425% | 0.06862% | 0.25407% |
| BNBUSDT | +0.00596% | 0.12272% | 0.33977% |
| SOLUSDT | -0.05006% | 0.09528% | 1.40117% |

**Economic implication, not a selected strategy:** median basis magnitudes are only about 0.006–0.050 percentage points, so a naive two-leg basis-convergence trade can easily be consumed by opening/closing spot and perpetual fees, slippage, financing/borrow, spread and funding. For scale only, **four fills at 4 bps each cost 16 bps before slippage**, not a measured spot fee schedule. Source viability does not establish executable positive expected edge. Do not tune signs, thresholds or windows from these diagnostics.

**Next gate:** independently verify spot taker/maker fee tiers, spot borrow and short availability (if applicable), perpetual funding, tradeable spread/depth and one-way two-leg inventory/execution accounting. Then preregister a genuinely new seven-slot V98 hypothesis, not revive any rejected PQ/PK/PL/PO or the earlier rejected strict 2022–2024 spot source. The separate 2022–2024 HQ masked source must be reconciled with the 2025 source before any full 2022–2025 basis research. No future holdout, V14/V15/V99, 2026+ data, Phase083, paper or live used.

**Exact funding mark blocker unchanged:** 13,524 Binance exchange-origin settlement `markPrice` values remain missing; authorized raw `/fapi/v1/fundingRate` pages with HTTP headers, request URLs, SHA256 and independently verified custody or an equivalent authorized exchange export are needed for final exact-cost attestation. Hourly envelopes remain proxies.

**Scope:** research/v98-independent-zero; V98 Independent files only. No V16 Frozen, V99, paper or other branches modified.
