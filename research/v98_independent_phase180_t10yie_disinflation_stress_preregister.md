# V98 Independent — Phase180 preregistration

Status: PREREGISTERED / ECONOMIC TRAINING-ONLY

## Hypothesis

A sustained decline in 10-year US breakeven inflation can proxy demand/disinflation stress. Under that state, reducing long crypto risk may improve downside robustness without requiring asset-specific prediction.

## Fixed signal and action

Source: Phase179 `T10YIE`, using only observations causally available no earlier than the next US business day.

Transformation: `delta63 = current_available_T10YIE - T10YIE_63_available_observations_ago`.

Variants are frozen to exactly two:
- CONTROL: existing V98 Independent training control exposure unchanged.
- DISINFLATION_GATE: when `delta63 < 0`, multiply control exposure by 0.50; otherwise 1.00.

No threshold sweep, alternative lookback, direction flip, asset-specific tuning, rescue variant, or combination with DTWEXBGS is allowed.

## Evaluation contract

Training window only: 2023-01-01..2025-12-31 with chronological yearly folds 2023/2024/2025. Validation and final holdout remain closed.

Report base, severe and supersevere realistic cost/funding scenarios; total return; max drawdown; Profit Factor; payoff; win rate; positive days; yearly folds; market regimes; per-asset contribution; tail contribution; concentration; turnover/exposure invariants; deterministic rerun identity.

Promotion requires the existing V98 Independent gates unchanged. Any gate failure is REJECT_NO_RESCUE. Passing training only authorizes the next existing validation gate; it does not authorize final holdout access.

V16/V99 information must not be used for tuning, selection or interpretation.
