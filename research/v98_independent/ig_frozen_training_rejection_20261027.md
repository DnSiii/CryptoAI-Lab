# IG immutable training rejection — 2026-10-27

**Decision: REJECT_IG_HISTORICAL_GROWTH_OR_MARGINAL.** IG is permanently rejected as a composed seven-slot V98 *training* candidate, not a complete validated/benchmarked/tradable engine. No sign, threshold, window, financing, gross, gate or ablation rescue. Opportunity passing alone does **not** promote any component or IG as a champion.

## Immutable evidence and strict firewall
- IG pre-result architecture locked in `ig_liquidity_impact_prereg_20261027.md` at commit `998162319ad47aad7eca0b52bebd1c83d040eabe` **before** source code and PnL.
- Exact pinned Clean-4 Dec-2022 through Dec-2024 native USD-M OHLC/quote/mark/signed funding from run `40064588623`. No OI/taker, XRP, 2025 holdout, 2026+, Phase083, V14/V15/V99 internals, Frozen or paper accessed.
- [Official IG source-first, 30-cell economic and five-book independent physical replay](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40492002920). Native source-only causal test passed: financed 2023 epochs Core/Opportunity/RV/Stress = 27/27/27/27, 2024 = 26/25/25/25. One 2024 optional epoch quarantined on zero/nonpositive native quote rather than imputed.
- 30/30 physical cells survived (five separately financed USD10k books, three costs, two funding orders, two OS). Independent artifact-only audit found **zero errors**, reproduced all cells across OS and rejected economic gates. Five independent each-hour signed funding, fees, slippage, mark and 81-corner settlement oracle jobs **all passed**.
- [Immutable artifact-only first-fault readout](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40492363216) reads the original `ig30-official-economic-summary` artifact from run 40492002920, not recomputed PnL. Funding orders are **not assumed economically redundant**; small differences were observed.

## Full IG net historical training (2023–2024; USD10k physical shared collateral)

| Measure | Base | Severe |
|---|---:|---:|
| Two-year CAGR | +70.7911% | +63.1444% |
| 2023 net return | +91.0074% | +81.8896% |
| 2024 net return | +52.8265% | +46.4292% |
| Max drawdown | 24.9038% | 26.1567% |
| Turnover USD | 402,952.36 | 381,886.04 |
| Signed funding USD | -1,630.70 | -1,524.87 |
| Fees USD | 201.48 | 763.77 |
| Slippage USD | 201.48 | 1,145.66 |
| Hourly net PF | 1.04711 | 1.04316 |
| Hourly net payoff | 0.97970 | 0.97985 |
| Hourly net win rate | 51.6631% | 51.5648% |
| Positive UTC days | 378/731 | 374/731 |
| Worst 1% hourly CVaR | -1.6270% | -1.6292% |
| Peak single-asset gross concentration | 76.7798% | 76.7798% |

## Full-minus-independent-ablation net log growth (original artifact, carried-before-fill)

| Sleeve | 2023 base | 2024 base | Combined base | 2023 severe | 2024 severe | Combined severe | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| Opportunity | +0.058508 | +0.031262 | +0.089770 | +0.047895 | +0.020409 | +0.068304 | PASS |
| Relative Value | +0.022640 | -0.070365 | -0.047724 | -0.101121 | -0.075283 | -0.176404 | FAIL |
| Stress/Recovery | -0.075693 | +0.047290 | -0.028403 | -0.073640 | +0.039471 | -0.034170 | FAIL |

Full annual net growth, minimum CAGR, severe drawdown and turnover passed. **RV and Stress/Recovery failed preregistered annual and combined marginal economic requirements**, including negative severe contributions. The source-only gate, physical survival and high in-sample CAGR are not approval.

**Next:** genuinely distinct composed-engine architecture with actual cost-aware *conditional* portfolio contribution, not a post-hoc IG adjustment or rescue. First pre-register, independently validate source, run physical training and independent marginal gates, then freeze candidate before any chronological validation or untouched future holdout. No external benchmark or live operation authorized.
