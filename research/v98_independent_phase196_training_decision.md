# V98 Independent — Phase196 training decision

Status: **REJECT_FAMILY_NO_RESCUE**

Scope: training-only 2023-01-01 through 2025-12-31. Validation and final holdout remain unopened. V16 and V99 are not used.

## Evidence

The frozen 8-spec idiosyncratic-volatility-shock relative-reversion family failed the training gate. The harvested report records no winner. A representative active spec `d24_s1.5_h12` returned -67.06% base with PF 0.632 and max drawdown -68.96%; every annual fold was negative (2023 -44.30%, 2024 -22.81%, 2025 -23.38%). Regime attribution was negative in bear, bull, and sideways conditions. Bottom-10 loss concentration was ~22%, so the failure is broad rather than attributable to a single removable tail event. Severe and supersevere costs also fail.

The report contains zero-activity cells for some stricter combinations; these are not evidence of robustness and are treated as failed/ineligible, not as PF=Infinity successes.

## Decision

Reject Phase196 family with no inversion, parameter rescue, or post-hoc threshold search. Do not open validation or final holdout. No champion is promoted.

## Scientific interpretation

Conditioning cross-sectional reversal on idiosyncratic volatility expansion does not isolate a stable mean-reversion edge in this training universe. The active configuration loses across all three chronological years and all broad regimes, which argues against merely retuning the shock threshold or holding horizon.

Next work must be scientifically distinct rather than a nearby rescue of volatility-shock reversal.
