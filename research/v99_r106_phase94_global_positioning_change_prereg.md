# V99 R106 Phase94 — Global positioning change preregistration

## Status
PRE-REGISTERED BEFORE ANY PHASE94 PNL.

Phase93 rejected the fixed continuation direction of the robust cross-sectional **level** of global account positioning. Phase94 changes the economic object rather than rescuing that result: it tests whether unusually rapid 24h changes in global long/short positioning are subsequently mean-reverting.

## Frozen hypothesis
- Source: Binance USD-M native daily metrics `count_long_short_ratio`, using only archives/dates already admitted by the Phase63 train-only data audit.
- Integrity: retain Phase92 SHA256/CHECKSUM + ZIP CRC/schema checks; do not fill missing archives.
- Transform: positive finite ratio -> log ratio; compute each asset's trailing 24-hour log change (`log_ratio[t] - log_ratio[t-24h]`); then shift the resulting feature by one hour before trading (`t-1`).
- Cross-section: at each simultaneous timestamp require >=10 observed assets; center 24h changes by the simultaneous median and scale by simultaneous MAD. Degenerate/non-finite MAD => zero exposure.
- Direction: **mean reversion**, fixed before PnL: `raw = -tanh(robust_z)`.
- Portfolio: L1-normalize cross-sectional raw weights, alpha gross fixed at 0.20.
- Costs: severe cost gate first, identical execution/evaluation machinery to Phase92/93.
- Selection: chronological train only through the Phase63 `train_end`; same temporal-fold/stable-train diagnostic. Holdout must not be listed, parsed, inspected, scored, or used for selection.

## Anti-overfit constraints
Exactly one Phase94 hypothesis. No grid, no threshold search, no horizon search, no sign flip, no rescue, no post-result parameter adjustment. The 24h horizon is precommitted as a natural one-day positioning-change horizon, not selected from results.

## Decision rule
If the existing stable-train gate passes, freeze this exact specification and advance unchanged to supersevere costs, regime matrix, benchmark envelope, and reproducibility before any untouched holdout gate. If it fails, permanently reject Phase94 and move to a genuinely different mechanism.

V16 Frozen and V99 Frozen are read-only and must remain byte-identical.
