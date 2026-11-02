# V98 Independent — VW frozen 2025 native carry physical rejection (2026-11-01)

**Binding decision: REJECT_VW_NATIVE_CARRY_GROWTH_FEASIBILITY. No V98 champion, no paper/live.** The preregistration `vw_native_carry_physical_prereg_20261101.md` was committed at `24d728e6e6ad87f0636aae3be76bb3c16e1ac086` BEFORE implementation, test or historical PnL. No rejected candidate is reopened. The VW monthly equal-notional all-Clean-4 spot-long/perp-short hedge is a standalone *economic falsification*, NOT a complete seven-slot V98 and NOT a 2022–2025 full-history validation.

## Physical execution and custody

- GitHub Actions run [41379650012](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41379650012), code commit `f57a708f4bb2fe54569883d9c1c8bc22ab8e7044`; job ended **failure by design** at the final preregistered *economic gate*, AFTER successful execution and independent replay. A red job is not a source/ledger integrity failure.
- Pinned official 2025 spot source SHA256 `069bec10906e476e19470b042d40ce3fa7d654228de9cff50bd53ad91ed74156`, pinned official NH USD-M receipt SHA256 `7ce4ec7e2a6980838fa0179729b3cc6da8f131806b03e070590146d6d6ca046b`. BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT all included, no ex-post selection.
- Artifact `v98-independent-vw-2025-exposed-physical-carry-not-engine`, ID `13112279859`, 30-day retention. Hourly ledger SHA256 `7af2f62eb54035a00c138a942e23f864b1908430ea371786fc0d15d1548c539f`. 6 fixed scenarios (three illustrative fee/slippage tiers, two funding boundary orders), 8,760 hours each, 48 monthly asset positions closed each, 4,380 native funding source events checked each.
- Independent replay PASS: **52,560/52,560 cash/spot/perp/equity identities**, all six scenarios, 288 total closed monthly positions, 4/4 semantic tamper controls rejected. Source and 2026+/holdout/benchmark/paper firewalls checked. This proves *internal arithmetic consistency*, not exact historical execution feasibility.

## Fixed scenario economics, initial USD 10,000, 2025 ONLY

| Scenario | 2025 net equity return (NOT multi-year CAGR) | Max hourly DD | Native funding net USD | Fees + illustrative slippage USD | Trade-level PF |
|---|---:|---:|---:|---:|---:|
| Base, funding before fill | **-0.92695%** | -1.035% | +90.25 | -181.94 | 0.2406 |
| Base, funding after fill | -0.92487% | -1.034% | +90.46 | -181.95 | 0.2429 |
| Severe, before | **-3.37954%** | -3.380% | +89.03 | -426.01 | 0.0000 |
| Severe, after | -3.37751% | -3.378% | +89.23 | -426.01 | 0.0000 |
| Supersevere, before | **-6.14025%** | -6.140% | +87.64 | -700.72 | 0.0000 |
| Supersevere, after | -6.13827% | -6.138% | +87.84 | -700.72 | 0.0000 |

The **observed base signed funding (+USD90.25)** fails to cover even the **illustrative base fee/slippage (-USD181.94)**. Residual spot/perpetual basis drift adds a small net negative. Under severe and supersevere costs, **0/48 closed asset-month positions won**, so this is not an engine-growth source under the frozen monthly equal-inventory policy. This rejects VW, not every conceivable carry mechanism. Do not select BTC/ETH ex-post or change month cadence, gross, sign, assets or fee assumptions to rescue VW.

## Scope, hard blockers and next decision

This physical simulation is limited to exposed 2025; it cannot be promoted to a seven-slot engine, cannot claim executable net PnL or independent prospective validation, and does not supply multi-year CAGR. Official hourly OHLC and signed funding rates are source-checked; funding event prices are conservative envelopes rather than exact settlement markPrice. Published or illustrative cost budgets are not historical account-specific fills. To validate a genuinely distinct future complete seven-slot system requires chronological 2022–2025 physical system backtest, separate validation, counterfactual sleeve marginal log growth, realistic cost stress, adverse intrabar and concentration/tail checks, immutable internal freeze, then external benchmarks. The exact 13,524 historical exchange-origin settlement `markPrice` values still require authorized /fapi/v1/fundingRate response bytes or equivalent attested exchange export, including request URLs, HTTP Date, UTC capture, SHA256 and independent custody; prior direct access returned HTTP 451. Historical account-specific spot and USD-M fees, bid/ask/depth/impact and collateral/liquidation evidence also remain external blockers for executable claims.

**Next:** reject monthly fixed carry, shift to a genuinely distinct **growth-oriented full seven-slot architecture** with independent core and complementary optional sleeves; preregister it before any historical result. Do not re-open VW or other frozen rejects. No V99, V16 Frozen, 2026+, Phase083, XRP, future holdout or paper accessed or changed.
