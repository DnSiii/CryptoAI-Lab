# V98 Independent — HF full-vs-ablation physical marginal cost forensics (2026-10-26)

**READ-ONLY FROZEN TRAINING ARTIFACT ANALYSIS.** Official [HF 30-cell run](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40389720461), `hf30-ubuntu-24.04-HF_full`, `HF_minus_opportunity`, `HF_minus_RV`, `HF_minus_stress` and `HF_core_only` independently funded USD10k, exact pinned native Clean-4 2023–2024 training, carried-before-fill order. No strategy recomputation or modification, no holdout, benchmarks, Frozen or paper. All 30 cells and five independent oracles passed mechanically, but HF was economically rejected. Numbers below are *counterfactual differences between full independently settled portfolios*, NOT additive attribution of an individual trade's causal PnL.

## Frozen full and ablation economic paths

| 2023–24 base path | Final USD NAV | Net log growth | Fees+slippage USD | Signed funding USD | Turnover USD |
|---|---:|---:|---:|---:|---:|
| Full | 43,259.74 | 1.464637 | 304.09 | -1,707.24 | 304,092.68 |
| Minus Opportunity | 43,146.94 | 1.462026 | 313.10 | -1,723.45 | 313,098.91 |
| Minus Relative Value | 38,212.10 | 1.340567 | 310.23 | -1,989.60 | 310,229.17 |
| Minus Stress | 43,530.82 | 1.470884 | 313.42 | -1,694.34 | 313,418.53 |
| Core only | 37,764.12 | 1.328774 | 329.64 | -2,057.48 | 329,646.40 |

## Marginal log growth and native cost differences: Full minus corresponding ablation

| Sleeve | Base marginal log growth | Severe marginal log growth | Base delta fees+slippage USD | Base delta signed funding USD | Base delta turnover USD |
|---|---:|---:|---:|---:|---:|
| Opportunity | +0.002611 | +0.003922 | -9.01 | +16.22 | -9,006.23 |
| Relative Value | **+0.124070** | **+0.132157** | -6.14 | +282.36 | -6,136.48 |
| Stress/Recovery | **-0.006247** | **-0.005184** | -9.33 | -12.90 | -9,325.85 |

**Interpretation constrained by counterfactuals:** Opportunity was **not** rejected because it necessarily increased direct fees or turnover: the full book actually spent ~USD9.01 less fees+slippage and turned ~USD9k less than its minus-Opportunity ablation. Its positive incremental net growth was simply too small for the immutable >+.02 economic gate. Stress likewise reduced observed fees+slippage and turnover relative to minus-Stress, yet lost net log wealth. Thus simply lowering turnover, fees or gross is insufficient to rescue these sleeves. Relative Value delivered the dominant measured incremental growth and had ~USD282 less net funding drag in the full book versus minus-RV. The funding difference is **not** a causal attribution of all RV profit: independent books reallocate capital and their paths compound differently.

The [separate governor algebra](v98_collateral_gross_hard_ceiling_20261026.md) shows a necessary all-long stressed collateral gross ceiling of ~0.7567x after-entry NAV; nominal 1.6–2.0x requests cannot bypass it. Future *new* complete architectures need truly orthogonal, positive marginal growth **per physically authorized dollar**, not cosmetic fee-only fixes or HF/HD/HG retuning. HF frozen rejected; HG separately source-only rejected; all previous rejections remain frozen. No 2025/2026+, XRP, Phase083, external benchmarks, V16/V99 Frozen or paper touched. No live trading.
