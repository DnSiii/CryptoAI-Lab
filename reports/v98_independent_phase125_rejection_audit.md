# V98 Independent — Phase125 rejection audit

Decision: **REJECT_NO_RESCUE**. This audit records the preregistered training result and does not alter parameters, gates, data, validation, or holdout state.

## Scientific result

Phase125 (US policy-uncertainty risk-on permission regime; USEPUINDXD, 28-observation rolling median, +2 calendar-day causal activation, low/normal=long, elevated=flat, frozen gross target 0.75) failed the training gate.

Training 2023-2025: total return -30.04%, CAGR -11.23%, max drawdown -44.77%, daily PF 0.941, payoff 1.028, win rate 32.69%, 358 positive / 391 negative days. Chronological folds: 2023 -27.45% / PF 0.799; 2024 +6.79% / PF 1.073; 2025 -10.45% / PF 0.939. Severe-cost return -43.03% / DD -50.58% / PF 0.895; supersevere -59.21% / DD -60.57% / PF 0.826.

The result is not a marginal miss: aggregate return/PF/DD, two of three yearly folds, severe and supersevere stress all fail. The always-long context benchmark returned +59.81% over the same training period, so the policy-uncertainty permission rule destroyed rather than improved training expectancy.

## Failure mechanism / concentration / regimes

Approximate regime contribution is positive in bear (+0.138) and slightly positive in bull (+0.033), but strongly negative in sideways (-0.403). Thus the dominant pathology is not simply inability to survive bear markets; the frozen gate removes/admits exposure poorly in sideways conditions.

Absolute asset-contribution concentration is also excessive: XRP contributes 48.24% of absolute contribution versus the preregistered 45% ceiling. Top-10 absolute-day share is 8.97%; worst-10 days sum -52.56% and best-10 +69.01%, confirming meaningful tail dependence without a compensating aggregate edge.

The execution audit observed max open gross 0.750009898 versus cap 0.75. This is a real contract failure under the frozen tolerance and is not relaxed retrospectively. It is not the reason for the scientific rejection: the hypothesis already fails multiple independent return, PF, DD, fold and stress gates by large margins.

## Integrity / anti-overfit decision

The run reconstructed only the frozen V98 canonical universe through 2025-12. The invariant suite passed 37/37 before execution. `validation=null`, `final_holdout=null`, `v16_used=false`, `v99_used=false`, `parameter_search=false`, `rescue_allowed=false`. No validation or final-holdout information was opened.

No threshold flip, alternate lookback, gross-cap relaxation, asset exclusion, lag change, or inverse-signal rescue will be attempted for Phase125. Policy-uncertainty Phase125 is closed. Current V98 Independent champion remains **none**.

## Next scientific step

Move to a genuinely distinct, preregistered V98 Independent hypothesis/family after checking the V98 experiment history for duplication. Any new data family must pass a DATA_ONLY integrity gate before values are used for hypothesis selection; any new trading hypothesis must freeze causality, folds, realistic funding/costs, severe/supersevere stress, DD/PF/payoff/win-rate/positive-days, regimes, concentration/tails and reproducibility before evaluation.
