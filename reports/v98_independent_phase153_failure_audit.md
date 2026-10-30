# V98 Independent — Phase153 failure audit

Decision: **REJECT_NO_RESCUE**. This audit does not reopen the hypothesis and does not inspect validation/final holdout.

## Temporal stability
- 2023: -3.8774%, PF 0.8713, MDD -11.1734%.
- 2024: zero exposure; a full fold contributes no evidence of edge.
- 2025: +4.6840%, PF 1.3573, MDD -4.3864%.
- Aggregate: +0.6250%, PF 1.0302, MDD -11.1734%.

The aggregate result is therefore not temporally replicated: one positive fold cannot compensate for one negative fold plus one inactive fold under the preregistered annual gates.

## Cost fragility
- Severe: +0.0815%, PF 1.0169.
- Supersevere: -0.7381%, PF 0.9969.

The already-small base edge crosses below zero under supersevere costs, so it lacks execution-cost margin.

## Regime and tail pathology
- Bull regime return-sum approximation is negative (-0.0230); bear is only slightly positive (+0.00236); sideways supplies the positive regime contribution (+0.03169).
- Bottom 10 negative days account for 49.57% of negative-day loss; top 10 positive days account for 36.95% of positive-day gain.
- Worst day is -6.35%, materially larger than the best day +3.61%.

## Asset concentration
Positive contribution is concentrated in BNB (60.18%), followed by BTC (19.94%), ETH (11.41%), SOL (8.47%), XRP (0%). This is diagnostic only; deleting assets or reweighting after observing attribution is prohibited rescue/tuning.

## Scientific disposition
Failure is multi-mechanism: temporal non-replication, supersevere cost failure, adverse tail asymmetry and contribution concentration. No sign flip, threshold/lookback search, asset deletion, regime exclusion, or DFF rescue is permitted. Phase153 is closed. Phase154 is scientifically distinct and DATA_ONLY.

Validation: untouched. Final holdout: untouched. V16 used: false. V99 used: false.
