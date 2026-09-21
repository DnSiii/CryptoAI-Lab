# V99 R106 Phase100 — Taker-flow impulse preregistration

Status: PRE-REGISTERED BEFORE PNL.

## Hypothesis
Cross-sectional **24h change** in aggressive taker imbalance contains short-horizon continuation information that is distinct from the rejected Phase96 level signal. Use Binance USD-M native `sum_taker_long_short_vol_ratio` only. For each symbol/hour compute `log(ratio_t) - log(ratio_t-24h)`, then shift the complete feature by **t-1** before any cross-sectional transform. At each timestamp compute simultaneous median/MAD z-score, map with fixed `tanh(z)`, L1-normalize, and target gross 0.20.

Direction is fixed ex ante: continuation toward positive taker-flow impulse. Minimum simultaneous universe: 10 assets. Missing archives are not filled. Every downloaded archive must pass SHA256 CHECKSUM and ZIP CRC. No grid, sign flip, rescue, threshold search, or post-result retuning.

## Gate
Selection is chronological train-only through 2024-01-18 with the existing temporal-fold/stable-train diagnostic under **severe** costs. Holdout must not be listed, parsed, inspected, or used. A PASS freezes this exact specification for downstream supersevere, regime matrix, benchmark envelope, and reproducibility gates before any holdout. A FAIL is permanent for this specification.

V16 Frozen and V99 Frozen are immutable and must remain byte-identical.