# V98 Independent CW — artifact-only economic failure decomposition (2026-10-24)

This postmortem reads the **immutable completed CW 20-cell economic artifact**; it does **not** rerun, retune or revive CW. Official artifact-only diagnostic: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40148253549 ; original 20-cell run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40148107038 .

## Annual full-minus-ablated net log growth (USD10k)
For each module, values are [2023, 2024], across carried-before-fill and new-after-fill native funding orders:

| Module | Base funding order A | Base order B | Severe order A | Severe order B |
| --- | --- | --- | --- | --- |
| Opportunity | [+0.004690, +0.079619] | [-0.004774, +0.080020] | [-0.002482, +0.071219] | [-0.014358, +0.071839] |
| Relative Value | [+0.021802, -0.032475] | [+0.033495, -0.037038] | [+0.024883, -0.043951] | [+0.034914, -0.047539] |
| Stress/Recovery | [-0.091245, -0.109861] | [-0.095587, -0.110713] | [-0.105464, -0.119692] | [-0.114984, -0.120555] |

**Main failure mechanism:** the directional Stress/Recovery overlay reduces net annual log growth in **both** years under **all** four fee/funding combinations. Opportunity is economically favorable in 2024 but not consistently in 2023; volume-lead Relative Value contributes in 2023 but loses in 2024. No module passes its preregistered robust annual marginal gate.

## Native execution cost and capacity diagnostics
- Full base: CAGR +39.2020%, max drawdown 24.9902%, gross/NAV peak 0.7761, single-asset concentration peak 83.36%, funding **-$1,583.77**, fees $260.21, slippage $260.21, turnover $520,415.30, hourly net PF 1.03693, positive UTC days 48.43%.
- Full severe: CAGR +28.3615%, max drawdown 29.1502%, gross/NAV peak 0.7710, single-asset concentration peak 83.67%, funding **-$1,418.67**, fees $940.95, slippage $1,411.43, turnover $470,476.39, hourly net PF 1.02811, positive UTC days 47.33%.
- Gross exposure never exceeded 0.78x NAV despite larger nominal budget requests. This is an **observed physical authorization result**, not proof the governor is incorrectly capped or that higher exposure would be safe. Do not relax the risk governor based on post-result return optimization.

## Implication for next independent hypothesis
Do **not** reweight, invert, or cosmetically rescue CW. The next independent architecture must target positive incremental annual net log growth of the **complete** portfolio, particularly by developing a genuine recovery/growth contributor rather than a persistently costly directional hedge, while preserving risk/funding/capacity constraints. If exploring a different governor, preregister and independently validate physical safety **before** any economic result. No untouched holdout, benchmark or paper access was performed.
