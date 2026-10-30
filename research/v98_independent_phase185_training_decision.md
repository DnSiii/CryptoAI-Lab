# V98 Independent — Phase185 training decision

Status: **PASS_TRAINING_FREEZE_FOR_VALIDATION**

Phase185 was executed exactly as preregistered on training 2023-01-01 through 2025-12-31. The deterministic GitHub Actions run completed successfully and its two executions were byte-identical. Validation and final holdout were not opened; V16/V99 were not used.

## Frozen candidate

`WALCL_4W_CHANGE = WALCL_t / WALCL_{t-4} - 1` on native weekly observations, conservatively available next UTC day. If change < 0, gross multiplier = 0.50; otherwise 1.00. No alternate threshold/lookback/sign/sizing and no rescue.

## Training evidence

WALCL gate base total return: **+57.5554%** versus CONTROL **+17.3040%**. Base PF **1.1699**, payoff **1.0580**, win rate **52.51%**, positive days **575/1095**, MDD **-18.1431%**. Severe return **+54.2904%**, PF **1.1621**, MDD **-18.2320%**. Supersevere return **+48.5826%**, PF **1.1483**, MDD **-18.3601%**.

Chronological folds remained positive: 2023 **+24.9314%** (PF 1.4191), 2024 **+22.2489%** (PF 1.1655), 2025 **+2.6623%** (PF 1.0296). The material deterioration in 2025 is a validation risk and must not be tuned away.

Regime return sums were positive in bear (+0.1464) and bull (+0.3992), but still negative in sideways (-0.0469), although less negative than CONTROL (-0.1045). Tail shares were not dominated by ten observations (bottom-10 negative share ~10.37%, top-10 positive share ~9.62%). Largest asset contribution share was SOL ~31.36%; concentration p95 top-1 weight share ~51.72%. No ruin; max open gross respected the existing ~0.35 cap.

## Decision

Freeze this exact candidate for one untouched confirmatory validation phase. Do not alter the WALCL transformation, threshold, multiplier, causal lag, underlying V98 stack, costs/funding, gross cap, or validation gates. No rescue is permitted if validation fails. Final holdout remains closed.