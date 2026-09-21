# V99 R106 Phase101 — Flow absorption preregistration

Status: PRE-REGISTERED BEFORE PNL.

## Hypothesis
A cross-sectional **24h aggressive-flow impulse that is not accompanied by open-interest expansion** can identify absorption/exhaustion rather than durable participation. Use only Binance USD-M native `sum_taker_long_short_vol_ratio` and `sum_open_interest_value`. For each symbol/hour compute `flow24 = Δ24h log(taker L/S)` and `oi24 = Δ24h log(OI value)`. Shift both completed features by **t-1** before any cross-sectional transform. At each timestamp independently robust-standardize each feature with simultaneous median/MAD, then define the fixed absorption score `z_flow - abs(z_oi) * sign(z_flow)`, map once with fixed `tanh(score)`, L1-normalize, and target gross 0.20.

Direction is fixed ex ante: continuation toward the residual aggressive-flow impulse after penalizing same-direction participation expansion. This is not a sign rescue of Phase100: the economic object is specifically flow unsupported by OI participation, and both inputs/direction are fixed before PnL. Minimum simultaneous universe: 10 assets. Missing archives are not filled. Every archive must pass SHA256 CHECKSUM and ZIP CRC. No grid, sign flip, rescue, threshold search, weighting search, or post-result retuning.

## Gate
Selection is chronological train-only through 2024-01-18 with the existing temporal-fold/stable-train diagnostic under **severe** costs. Holdout must not be listed, parsed, inspected, or used. A PASS freezes this exact specification for downstream supersevere, regime matrix, benchmark envelope, and reproducibility gates before any holdout. A FAIL is permanent for this specification.

V16 Frozen and V99 Frozen are immutable and must remain byte-identical.