# V98 Independent — Phase180 training decision

Status: **PASS_TRAINING_FREEZE_FOR_VALIDATION**.

Scope: training only, 2023-01-01 through 2025-12-31. Validation and final holdout remain unopened. V16/V99 were not used.

## Frozen hypothesis
T10YIE 63-observation disinflation-stress gate; causal availability is next US business day; same-day use forbidden; exposure gate fixed at 0.50/1.00. No parameter/lookback/threshold search and no rescue.

## Training evidence
CONTROL base: total return 17.303993%, CAGR 5.462940%, MDD -19.156393%, PF 1.071091, payoff 1.012115, win rate 51.4155%, positive days 563/1095. Severe return 15.290569%; supersevere 11.421323%.

DISINFLATION_GATE base: total return 73.999095%, CAGR 20.272708%, MDD -14.882026%, PF 1.237158, payoff 1.152062, win rate 51.7808%, positive days 567/1095. Severe return 69.927078%, PF 1.226540; supersevere return 63.057500%, PF 1.208257. No ruin.

Chronological folds for gated variant: 2023 +26.814045%, PF 1.390924, MDD -8.3513%; 2024 +30.119714%, PF 1.308734, MDD -10.3939%; 2025 +5.001090%, PF 1.048845, MDD -14.8820%. All three folds are positive, but 2025 deterioration is material and must be treated as a validation risk rather than tuned away.

Regime return-sum approximation: bear +0.080615; bull +0.470667; sideways +0.038864. Sideways improved from CONTROL -0.104495 to positive.

Concentration/tails: largest asset contribution share SOL 30.40%; BTC 17.25%, ETH 11.71%, BNB 17.02%, XRP 23.61%. Mean top-1 weight share 25.44%, p95 49.09%. Top-10 positive-day share 10.38%; bottom-10 negative-day share 12.10%. No single-asset or extreme-tail dominance sufficient to reject training evidence.

Gross exposure audit: frozen open-gross cap is 0.35; observed `max_open_gross` is 0.3500000000000001 (floating-point representation). Reported intraperiod `max_gross` reaches 0.3571225896 and is retained explicitly as a path-risk diagnostic; it is not silently reinterpreted or removed.

## Decision
Promote exactly the frozen Phase180 specification to the next validation gate. Do not alter the 63-observation transform, 0.50/1.00 exposure rule, causal lag, universe, costs/funding, or gates after seeing training results. Do not open final holdout. If validation fails, reject without rescue/tuning on validation.
