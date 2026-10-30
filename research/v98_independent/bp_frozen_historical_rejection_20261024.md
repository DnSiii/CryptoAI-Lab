# V98 Independent BP — irrevocable original training rejection (2026-10-24)

**Decision: REJECT_BP_HISTORICAL_GROWTH_OR_MARGINAL.** This is NOT a qualified complete V98 engine, not a champion, not validated out-of-sample and not authorized for paper/live execution. The preregistered architecture is frozen in [BP preregistration](bp_preregistered_architecture_20261024.md). No post-result change to signals, parameters, sign, windows, fees, costs or portfolio exposure is allowed to rehabilitate BP.

## Original immutable evidence
- Training workflow: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40083657025 at commit `fa00b96abd756d85fc223fdf6a994c0af80719ad`.
- Initial attempt https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40083577742 failed BEFORE economic testing because a mechanical namespace substitution corrupted `bounds` to `bpunds`, `bool` to `bpol`, and `borrow` to `bprrow`. Corrected mechanical naming only before any successful economic run. Initial failure is NOT economic evidence.
- 5 paths x 3 capital scales x 3 cost tiers x 2 funding orders = **90/90 physically surviving original training cells**, exactly identical results on Ubuntu 22.04 and 24.04. Independent original-receipt arithmetic: **180/180 cells checked, zero errors**. Workflow success is NOT an economic pass.
- Independent raw native-event replay in the same workflow: 4 fee/order full-path combinations x 16,272 settlement hours = **65,088 reconstructed hourly settlements**, 8,136 native event slots per path, 9,144 source funding events authenticated, and 81 OHLC intrabar corners each hour; all four cases passed. These verify accounting and physical viability only, NOT alpha or prediction.

## Original full USD 10,000, carried-before-fill, 2023/24 TRAINING ONLY

| Cost | 2023 CAGR | 2024 CAGR | 2y CAGR | Max DD | Turnover USD | Fees USD | Slippage USD | Signed funding USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Base | +126.827% | +17.376% | **+63.095%** | 28.385% | 477,688.23 | 238.84 | 238.84 | -782.79 |
| Severe | +118.571% | **-3.506%** | +45.145% | 25.805% | 561,783.75 | 1,123.57 | 1,685.35 | -822.79 |
| Supersevere | +99.126% | **-20.205%** | +25.974% | 32.515% | 440,765.85 | 2,203.83 | 4,407.66 | -355.34 |

Base physical fill hours 38; Profit Factor 1.08445, payoff 1.04427, hourly win rate 50.944%, 110/731 positive UTC days. The two-year severe CAGR is **not** sufficient: preregistration demands both annual folds positive under base and severe for both funding orders.

## Original full minus original ablation: annual net log growth (USD10k, carried-before-fill)
| Sleeve | 2023 base | 2024 base | 2023 severe | 2024 severe |
|---|---:|---:|---:|---:|
| Opportunity | -0.131539 | -0.087612 | -0.156835 | -0.287720 |
| Relative Value | -0.046485 | +0.012587 | -0.062535 | -0.202490 |
| Stress/Recovery | +0.000000 | -0.002825 | +0.000000 | -0.000976 |

All three marginal gates **FAIL**. Zero is not strictly positive. The original 2024 severe annual growth gate **FAILS** under both funding orderings. Consequently BP is permanently rejected regardless of its impressive two-year training CAGR. Do not promote ablations or use 2025 data to rescue.

## Scope and next decision
Pinned BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT 1h Dec2022–Dec2024 only, authenticated native 8h funding and conservative mark bounds. **2025 holdout untouched**; 2026+ excluded; XRP quarantined; Phase083 holdout ineligible; V16/V99 Frozen, V99 branch/workflows/reports/paper untouched. No V14/V15/V99 signal, architecture or benchmark used.

Next research must be a genuinely distinct full seven-slot hypothesis that addresses severe-cost annual growth and economically additive sleeves *before* any holdout or external benchmark. Do not relabel or tune BP. Training return is not proof of future profitability.
