# V98 Independent — Phase229 postmortem

Decision: **REJECT_FAMILY_NO_RESCUE**.

This note applies only to the corrected causal Phase229 run harvested at `cd06e1f25995c47d28ed16810632c290d3a683bd` (payload SHA256 `bd8590e3b435567ea436a50539294081fdf1d50f209b4bea80b678cf3b31069e`). The earlier pre-fix run remains quarantined and is not evidence.

## Integrity / reproducibility
- Training-only canonical data ends before 2026-01-01; holdout remains unopened.
- Decision at open(t) uses samples ending no later than open(t-1).
- Costs remain frozen at base/severe/supersevere = 7/14/28 bp.
- Funding is point-in-time and training-only.
- Two evaluator executions were byte-identical before validation/harvest.
- Independent mechanical validator returned zero survivors.

## Failure mechanism
The family fails economically rather than through a narrow concentration accident. For `hour_of_day_lb12_h1` in 2023 base, return is -99.568%, PF 0.632, max drawdown -99.575%, win rate 38.69%, positive days 16.16%, and median trade -2.64 bp. Bear, bull, and sideways regime returns are all negative. Asset PnL contributions are negative across BTC, ETH, BNB, SOL, and XRP, with max asset concentration only ~24.8%, so the loss is not explained by one asset. Severe and supersevere costs monotonically worsen the economics.

The same pathology persists into 2024 for the representative spec: base return -99.884%, PF 0.628, max drawdown -99.884%, win rate 40.19%, positive days 20.22%; all three regimes remain negative. This is incompatible with a robust tradable time-of-week/hour effect under realistic costs.

## Scientific decision
No rescue, regime filter, asset deletion, cost relaxation, threshold retuning, or holdout inspection is permitted. Phase229 is closed as a rejected family. Champion remains unchanged.
