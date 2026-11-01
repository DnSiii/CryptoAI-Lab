# V98 PU — frozen historical rejection (2026-11-01)

**REJECT_PU_TRAINING. No V98 engine approved.** Pre-PnL preregistration commit `fa9ac30ea95ef3367c2adaa3817a7ca950e304ac`; complete [Actions run 41358786449](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41358786449). The workflow failed at its **intended economic gate**, not at physical execution or independent accounting. The entire 2023–2025 sample is exposed TRAINING, not validation or holdout.

| Full PU, carried-before-fill | Base | Severe | Supersevere |
|---|---:|---:|---:|
| CAGR | 14.21% | 8.64% | 3.20% |
| Max DD | -51.82% | -54.45% | -57.11% |
| 2023 | 82.09% | 74.79% | 67.27% |
| 2024 | -15.96% | -20.87% | -25.77% |
| 2025 | -2.65% | -7.29% | -11.49% |
| Turnover USD, initial 10k | 1635758 | 1514843 | 1398700 |
| Fees + slippage USD | 981.45 | 3029.69 | 4895.45 |
| Native funding cash USD | -996.79 | -946.06 | -896.20 |

**Physical and independent proof:** 30/30 scenarios completed; 157 weekly causal decisions; 26,303 hourly cash/fill/funding records reconciled with zero discrepancies; independent signal/allocator mismatches 0 (max error 1.13e-17); independent receipt 60/60 arithmetic checks, all 24 economic failures reproduced and 4/4 tamper cases rejected. Original immutable Actions artifacts: full receipt ID 13104815575, independent audit ID 13104741056. Repository snapshots alongside this report.

**Binding economic failures:** CAGR base 14.21% below >80%; severe 8.64% below >60%; severe DD -54.45% below -45% gate; severe 2024 and 2025 negative; turnover base/severe exceeds USD1m. Base leave-one-out marginal log growth Opportunity -0.016379, RV 0.013737, Stress 0.000000; severe -0.023785 / 0.012782 / 0.000000; none reaches +0.02. Raw optional activations Opportunity/RV/Stress 18/1/1/157. Hourly NAV PF/payoff/win rate are not independently verified trade-level metrics.

**PU permanently rejected; no rescue** by changing signals, forecast, half-life, funding, weights, thresholds, cost, gross or gates. Core-only and ablations cannot become PU champions. No external benchmark, XRP, 2026+ training, Phase083, holdout, V16/V99 Frozen or paper touched. Only V98 Independent files/workflow modified.

**External blockers to finished V98:** 13,524 exact Binance USD-M exchange-origin funding-event `markPrice` need authorized raw `/fapi/v1/fundingRate` response pages with URL, original bytes, original HTTP Date, UTC capture, SHA256 and independently attested custody, or equivalent authorized exchange-origin export; prior direct historical API HTTP 451. Hourly conservative mark envelope is only an exploratory proxy. Historical account-specific fees, executable bid/ask/depth/impact, collateral/liquidation evidence and independent future validation/paper remain missing. No real/paper trading authorized.

**Next:** seek genuinely different structural net-growth economics and positive optional marginal contributions, with pre-PnL preregistration; do not reopen PU.
