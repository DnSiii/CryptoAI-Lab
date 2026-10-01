# V98 Independent — Phase204 decision

## Decision

**REJECT_FAMILY_NO_RESCUE.**

Phase204 tested the preregistered relative-realized-volatility expansion + CLV continuation family on training-only calendar folds 2023, 2024 and 2025. The deterministic workflow completed successfully, including canonical-data rebuild, temporal/structural firewall, two byte-identical evaluator runs, and V98-only report harvest.

## Evidence

The family is not economically viable at the frozen base cost, before considering harsher stress. Representative/high-activity specifications already show Profit Factor below 1, negative returns and material drawdowns. Examples include `rv12_x125_h3` in 2023 (PF 0.861, return -35.6%, MDD -41.0%) and `rv12_x125_h6` in 2023 (PF 0.906, return -33.3%, MDD -43.3%). Raising the expansion threshold reduces activity but does not create a broad edge: `rv12_x175_h3` 2023 PF is 0.898 and `rv12_x175_h6` 2023 PF is 0.928. The 24h family likewise starts below unity (`rv24_x125_h3` PF 0.842; `rv24_x125_h6` PF 0.862), while stricter variants remain negative rather than revealing a robust low-turnover pocket.

Cost stress worsens the same failure mechanism. In the `rv12_x125_h3` 2023 example, PF falls from 0.861 base to 0.702 severe and 0.491 supersevere, with return falling from -35.6% to -65.4% and -90.0%. Bear, bull and sideways decompositions are all below PF 1 in that fold. The failure is not attributable to one asset: all five assets are negative in that representative fold and maximum absolute-return concentration is ~30%.

The reported trade-tail quantiles equal the fixed transaction-cost debit in many cells (`p01 == p99 == -cost`). This is a diagnostic limitation of the current trade-tail extraction (it samples entry-bar PnL rather than full holding-period trade PnL), so those tail fields are **not** used as positive or negative evidence for promotion. The portfolio/fold/regime/asset metrics are sufficient to reject the family without relying on that flawed tail diagnostic. Future evaluators should aggregate complete trade PnL before computing trade-tail quantiles.

## Integrity / anti-overfit

- Frozen 8-spec grid was evaluated without threshold rescue, inversion, asset deletion or regime selection.
- Features/entries remained causal through t-1.
- Only training data `<2026-01-01` were rebuilt/read; validation/final holdout remain untouched.
- Severe and supersevere costs and funding handling were preserved.
- Workflow completed two deterministic runs and required identical SHA256 output.
- V16 Frozen, V99 Frozen, V99 research/workflows/reports and V99 paper state were not used for selection and were not modified.

## Research consequence

Do not rescue Phase204. The next hypothesis must be scientifically distinct rather than another volatility-threshold refinement. Phase205 is preregistered separately as a causal BTC-to-alt lead/lag underreaction test, motivated by information propagation rather than single-asset continuation/reversal.
