# V98 Independent — Phase150 WTI risk-off audit

Decision: **REJECT_NO_RESCUE**.

## Frozen evidence
- Training total return: -3.7337%; daily PF: 0.9746; max drawdown: -18.2667%; payoff: 1.0686; positive days: 197/1095.
- 2023: -8.8593%, PF 0.7280, MDD -12.2877%.
- 2024: -1.2794%, PF 0.9809, MDD -10.5217%.
- 2025: +7.3515%, PF 1.3110, MDD -6.7672%.
- Severe: -7.2850%, PF 0.9391, MDD -19.6954%.
- Supersevere: -12.4461%, PF 0.8880, MDD -23.0527%.

## Independent failure-mechanism audit
The hypothesis is temporally unstable: only 2025 is positive while 2023 and 2024 fail both return and PF gates. Higher friction monotonically worsens the already-negative aggregate result, so costs amplify rather than create the failure.

Regime attribution does not support a robust all-regime edge: approximate return contribution is negative in bear (-0.0201) and sideways (-0.0145), with only bull positive (+0.0091). Tail concentration is meaningful but not singular: bottom-10 negative days account for 22.31% of negative-day loss while top-10 positive days account for 21.38% of positive-day gains. This is not a one-event pathology that can be defensibly removed.

Asset-positive contribution is entirely BTC/ETH among positive contributors (BTC 53.39%, ETH 46.61%), but post-hoc asset deletion/reweighting is prohibited. No sign flip, threshold/lookback tuning, regime exclusion, asset exclusion, or rescue is permitted.

## Integrity
Validation and final holdout remain unopened. V16 and V99 were not used. Phase149 dependency remains PASS_DATA_ONLY with reacquisition hash verified. Deterministic replay and workflow invariants passed.

## Decision
Close the WTI risk-off family as REJECT_NO_RESCUE. The next experiment must be scientifically distinct and preregistered before economic inspection.