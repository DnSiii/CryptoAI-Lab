# V98 Independent EC — frozen artifact-only capital displacement forensics (2026-10-25)

This analysis reads **only the immutable EC official Ubuntu-24.04 path receipts** from [run 40213569443](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40213569443), and recomputes differences from those frozen outputs. No rerun, OHLC/source exploration, 2025 holdout, external benchmark, tuning, sleeve rescue or live operation. EC remains **permanently rejected**.

## Base costs and opportunity cost, USD10k, carried-before-fill
- **Core only:** CAGR 57.161%, net gain USD14,714.84, turnover USD170,541.89, fees+slippage USD170.54, funding -USD1,836.32, DD 31.57%.
- **Complete EC:** CAGR 47.796%, net gain USD11,855.45, turnover USD587,429.42, fees+slippage USD587.43, funding -USD1,291.51, DD 33.16%.
- The complete portfolio traded **USD416,887.53 more notional** and earned **USD2,859.39 less final NAV** than the core-only path. Funding improved USD544.81, but did not compensate for displacement and trading losses.

## Physically settled leave-one-out deltas, full minus without sleeve
| Sleeve | Base Δ final NAV | Base Δ turnover | Base Δ fees+slippage | Base Δ funding | Severe Δ final NAV | Severe Δ fees+slippage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Opportunity | +USD111.15 | +USD1,642.19 | +USD1.64 | -USD7.50 | +USD91.44 | +USD7.80 |
| Relative Value | **-USD644.27** | +USD73,733.61 | +USD73.73 | +USD40.21 | **-USD984.50** | +USD298.79 |
| Stress/Recovery | **-USD1,185.31** | +USD73,174.74 | +USD73.17 | +USD74.73 | **-USD1,465.32** | +USD318.37 |

The leave-one-out final NAV deltas are **conditional**, non-additive contributions: removing one sleeve changes subsequent cash, risk authorization and path dependence. They must not be summed to explain the core/full difference. RV and Stress harm annual net log growth in both 2023 and 2024 and both funding orderings. Importantly, the **base incremental fee+slippage for RV/Stress (USD74 each) is far smaller than their NAV destruction (USD644/USD1,185)**, while funding deltas are positive. The dominant issue is missing net economic edge / core capital displacement, not simply excessive fee assumptions.

**Decision:** no EC component is promoted; no rejected source is reused as a champion. Next distinct complete architecture should target independently motivated, positive marginal return sources before adding turnover, and should verify physically settled contribution against a high-growth core. The official precommitted CAGR >50% base gate and both RV/Stress marginal gates failed. Frozen, V99, paper and sealed 2025 remain untouched.
