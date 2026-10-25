# DJ rejected engine — independent frozen-artifact native cost attribution (2026-10-25)

**Read-only diagnostic, not a candidate rescue.** Frozen official native 20-cell receipt: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40174247771 . Artifact-only forensic workflow: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40174502827 . No re-execution, signal tuning, 2025, external benchmarks or paper.

On USD10,000 starting NAV (two-year 2023/2024 training, carried-before-fill ordering):

| Full system | Base | Severe |
| --- | ---: | ---: |
| Final NAV | $11,214.97 | $8,040.16 |
| CAGR | +5.8966% | -10.3264% |
| Turnover | $847,226.61 | $706,929.38 |
| Native fees | $423.61 | $1,413.86 |
| Slippage | $423.61 | $2,120.79 |
| Fees + slippage | $847.23 | $3,534.65 |
| Signed funding | -$150.72 | -$123.07 |
| Max drawdown | 14.97% | 24.52% |

Severe-minus-base execution fees/slippage **+$2,687.42**, despite severe turnover being **$140,297.23 lower** due to changed physical authorizations. This is a counterfactual comparison of two complete physical paths, **not** a causal attribution of the entire final-NAV difference to friction alone.

Marginal annual log growth (full minus ablation; carried-before-fill):
- Opportunity: base 2023 +0.15389, 2024 +0.00787; severe 2023 +0.11687, 2024 **-0.01329**.
- Relative Value: base 2023 **-0.04326**, 2024 **-0.05456**; severe 2023 **-0.10196**, 2024 **-0.12575**.
- Stress: base 2023 **-0.07505**, 2024 +0.03260; severe 2023 **-0.08263**, 2024 +0.02522.

**Decision remains REJECT_DJ.** This receipt rules out cosmetic fee adjustments or a gross-PnL claim. Subsequent hypotheses must be distinct complete architectures with native-cost survival and positive portfolio marginal contribution. This is artifact-only accounting, not independent event-level replay.
