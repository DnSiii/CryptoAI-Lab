# V98 Independent — Phase177 Phase176 failure audit

Status: CLOSED / REJECT_NO_RESCUE

Scope: audit only of Phase176 persisted training evidence. No validation or final holdout opened. No V16/V99 evidence used.

## Evidence audited

Phase176 fixed hypothesis: DTWEXBGS 63-observation USD-strength macro gate, causal availability next US business day, no same-day use, no lookback/threshold/parameter search.

The persisted gate is REJECT_NO_RESCUE solely because `gross_cap` failed. The observed `max_open_gross` for MACRO_GATED is 0.3500115761686837 against the frozen 0.35 cap. This is an economic/risk-contract gate, not the workflow numerical-tolerance invariant corrected afterward; therefore Phase176 remains rejected and must not be rescued or promoted.

## Independent failure-mechanism audit

The rejected candidate nevertheless provides useful falsification evidence about the macro family:

- Training total return: MACRO_GATED +69.8522% vs CONTROL +17.3040%.
- Training PF: 1.2151 vs 1.0711; MDD: -16.6733% vs -19.1564%; payoff: 1.1274 vs 1.0121.
- Severe return +65.8756%, PF 1.2051, MDD -16.7745%; supersevere return +59.2556%, PF 1.1882, MDD -16.9265%.
- Chronological folds remained positive for MACRO_GATED: 2023 +33.8627% / PF 1.3664; 2024 +21.3298% / PF 1.2575; 2025 +4.1270% / PF 1.0393. The weakening into 2025 is material and argues against treating the training aggregate as sufficient evidence.
- Regime return sums were positive in bear, bull and sideways for MACRO_GATED; CONTROL sideways was negative. This supports the *family* as scientifically interesting but does not override the failed frozen gate.
- Asset contribution was not single-asset dominated: largest contribution SOL 33.54%, then XRP 18.97%, BNB 16.46%, BTC 16.12%, ETH 14.91%.
- Tail concentration was not extreme: bottom-10 negative-day share 9.26%, top-10 positive-day share 10.32%.
- Positive days improved only modestly (568/1095 vs 563/1095), so most aggregate improvement came from payoff / loss-shape changes rather than a dramatic hit-rate increase.

## Decision

Phase176 stays `REJECT_NO_RESCUE`. Validation and final holdout remain unopened. No cap relaxation, clipping, parameter adjustment, alternate threshold, alternate lookback, or post-hoc variant is allowed from Phase176.

## Next hypothesis discipline

The next experiment must be scientifically distinct rather than a Phase176 rescue. A justified direction is to inspect a new orthogonal macro/data family under DATA_ONLY rules first, with causal publication timing and reproducibility established before any economic test. The Phase176 DTWEXBGS family is archived as informative-but-rejected evidence and is not eligible for immediate retuning.
