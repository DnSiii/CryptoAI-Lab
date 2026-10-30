# V98 Independent — Phase144 rejection audit

Decision: **REJECT_NO_RESCUE**.

## Frozen hypothesis

Phase144 tested the preregistered 20-accepted-observation SP500 risk-on state with a one-calendar-day economic-use lag, equal-weight long BTC/ETH/BNB/XRP/SOL, 0.45 target gross and 0.50 open-gross cap. No parameter search or rescue is permitted.

## Evidence

The aggregate training result was positive (+70.81%, PF 1.176, max drawdown -28.78%), and both cost stresses remained positive: severe +64.02% / PF 1.163; supersevere +52.74% / PF 1.141. This does **not** override the chronological fold gate.

The decisive failure is 2025: return -13.06%, PF 0.904, payoff 0.869, max drawdown -28.78%. 2023 (+10.32%, PF 1.131) and 2024 (+77.71%, PF 1.450) pass their return/PF gates. The large dispersion across years indicates temporal instability rather than a cost-only failure.

Regime attribution is consistent with that diagnosis: approximate contribution is strongly positive in bull (+0.602), only mildly positive sideways (+0.063), and negative bear (-0.055). The family therefore does not demonstrate robust all-regime permission.

Concentration does not explain the rejection. Positive contribution shares are distributed across assets (largest SOL 23.49%, XRP 23.03%); top-10 positive-day share is 11.58%, so the aggregate result is not a small-tail artifact.

Reproducibility/causality controls passed in CI: Phase143 was reacquired with the governing hash, Phase144 was replayed deterministically, the causal contract tests passed, validation/final holdout remained null, and V16/V99 were not used.

## Scientific decision

Do not tune SP500 lookback, threshold, lag, sizing, direction, or combine it with observed crypto outcomes to rescue this family. Phase144 is closed as REJECT_NO_RESCUE. Any next experiment must be a scientifically distinct preregistered family and must preserve the unopened validation/final holdout policy.
