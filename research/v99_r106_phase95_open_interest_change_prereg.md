# V99 R106 Phase95 — Open-interest change preregistration

## Status
PRE-REGISTERED BEFORE ANY PHASE95 PNL.

Phase94 rejected mean reversion in 24h changes of the global account long/short ratio. Phase95 changes both the native field and economic mechanism rather than rescuing that result: it tests whether unusually strong 24h expansion/contraction in aggregate USD-M open-interest value contains cross-sectional continuation information.

## Frozen hypothesis
- Source: Binance USD-M native daily metrics `sum_open_interest_value`, using only archives/dates already admitted by the Phase63 train-only data audit.
- Integrity: retain Phase92 SHA256/CHECKSUM + ZIP CRC/schema checks; do not fill missing archives.
- Transform: positive finite open-interest value -> log; compute trailing 24-hour log change; then shift the feature one full hour before trading (`t-1`).
- Cross-section: at each simultaneous timestamp require >=10 observed assets; center changes by simultaneous median and scale by simultaneous MAD. Degenerate/non-finite MAD => zero exposure.
- Direction: **continuation**, fixed before PnL: `raw = +tanh(robust_z)`. Economic rationale: relative capital/open-interest expansion is treated as participation confirmation, while contraction is treated as relative de-risking.
- Portfolio: L1-normalize cross-sectional raw weights, alpha gross fixed at 0.20.
- Costs: severe cost gate first, identical execution/evaluation machinery to Phase92-94.
- Selection: chronological train only through Phase63 `train_end`; same temporal-fold/stable-train diagnostic. Holdout must not be listed, parsed, inspected, scored, or used for selection.

## Anti-overfit constraints
Exactly one Phase95 hypothesis. No grid, no threshold search, no horizon search, no sign flip, no rescue, no post-result parameter adjustment. The 24h horizon is precommitted as a natural one-day participation-change horizon.

## Decision rule
If the existing stable-train gate passes, freeze this exact specification and advance unchanged to supersevere costs, regime matrix, benchmark envelope, and reproducibility before any untouched holdout gate. If it fails, permanently reject Phase95 and move to a genuinely different mechanism.

V16 Frozen and V99 Frozen are read-only and must remain byte-identical.
