# V98 Independent — Phase181 frozen validation decision

Status: **REJECT_VALIDATION_NO_RESCUE**

Candidate: Phase180 frozen T10YIE 63-observation disinflation-stress gate (0.50).
Validation window: 2026-01-01 through 2026-07-31 only. Final holdout begins 2026-08-01 and remains unopened.

## Confirmatory result

The preregistered candidate failed untouched validation and is rejected without rescue or retuning.

- Base total return: -12.286988%
- Daily Profit Factor: 0.784666
- Max drawdown: -15.293204%
- Daily payoff: 0.822756
- Daily win rate: 48.8152%
- Positive days: 103 / 211
- Severe return: -12.488465%
- Supersevere return: -12.791212%
- Max open gross: 0.340191 (within 0.35 cap)

Failed preregistered gates: validation_return<=0; validation_pf<=1.02; severe_return<=0; supersevere_return<=0.

## Independent failure audit

This is broad economic failure, not a single-tail or concentration artifact. Bear, bull, and sideways regime return sums were all negative. Five asset contribution shares were all negative. Top-10 positive-day share was ~36.77% and bottom-10 negative-day share ~31.43%, so the loss is not explained by one isolated tail. Concentration was modest (mean top-1 weight share ~21.55%, p95 ~22.98%).

Monthly path: Jan -4.84%, Feb -4.39%, Mar +0.36%, Apr +1.24%, May -0.37%, Jun -5.96%, Jul +0.91%. Only 3/7 months were positive. The frozen gate also underperformed CONTROL (-9.08%, PF 0.813) in validation, despite its strong 2023-2025 training result.

Interpretation: the Phase180 T10YIE overlay did not generalize out of sample. Training promotion is revoked. No parameter change, threshold search, lookback search, rescue, or holdout inspection is permitted from this result.

## Integrity

Workflow run 36499327979 completed successfully. Canonical data were rebuilt only through validation; Phase181 executed twice with byte-identical output; final_holdout=null; final_holdout_untouched=true; parameters_frozen_from_phase180=true; v16_used=false; v99_used=false.

Decision: retire this candidate and return to scientifically distinct training-only hypothesis generation. The final holdout remains sealed and cannot be used to choose the next hypothesis.
