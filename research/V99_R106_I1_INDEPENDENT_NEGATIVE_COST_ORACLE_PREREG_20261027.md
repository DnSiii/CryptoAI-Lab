# V99 I1 — independent native-coin oracle: negative-cost injection closure (2026-10-27)

**SOURCE_ONLY/HOLD — NO PROMOTION.** This is a falsification/integrity correction in the independently implemented accounting oracle; it is not a new strategy, TRAIN, alpha trial, native-fee authentication or economic result.

## Predeclared defect and change
The primary native-coin wallet rejects negative opening fees/slippage and negative single-position delivery fees. The independent replay oracle currently rejects negative *mark* costs and negative *batch* delivery fees, but it does not reject (a) a negative `entry_fees_coin` or `entry_slippage_coin` on `open`, or (b) a negative `delivery_fee_coin` on `settle`. If a forged trace and its observed balance are changed consistently, a negative cost can become an artificial credit in the reference calculation.

Before implementation, fix only the independent oracle to reject both classes with distinct explicit errors; add adversarial tests that first construct a self-consistent forged observed balance (not merely a mismatched observation) and require rejection for severe and supersevere. Preserve all existing valid event replay and all strategy parameters, source partitions and holdout seals.

## Acceptance and boundaries
Run the actual GitHub Actions native-coin replay workflow and harvest final conclusion; verify independent oracle still accepts valid synthetic traces and rejects forged negative costs. A green CI proves only the synthetic accounting guard. No original 2021–2023 licensed BTC/ETH options lifecycle, historical native fee/margin, authenticated fills or economic TRAIN exists yet. Never touch Frozen, paper, champion, validation, holdout, orders or dashboard PnL.
