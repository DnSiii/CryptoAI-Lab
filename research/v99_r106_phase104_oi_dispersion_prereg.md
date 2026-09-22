# V99 R106 Phase104 — OI dispersion train-only preregistration

Precommitted before any Phase104 PnL is computed.

## Hypothesis
The rejected Phase102 OI impulse and Phase103 OI acceleration treated participation growth as directional continuation. Phase104 instead tests a distinct cross-sectional structural hypothesis: unusually large absolute 24h OI participation changes identify crowded/repricing assets, and the *signed price direction* of that participation change supplies direction. Alpha is price 24h return sign times cross-sectional magnitude of absolute 24h log-OI change.

## Fixed specification
- Source: Binance USD-M daily metrics `sum_open_interest_value`, checksum/CRC verified; only archives already admitted by the Phase63 train data audit.
- OI feature: `abs(delta24(log(OI)))`.
- Direction: sign of causal 24h close return.
- Raw alpha: `sign(ret24) * robust_z(abs(delta24(logOI)))`.
- Entire alpha shifted by one hour before execution (causal t-1).
- Cross-sectional robust z: hourly median/MAD; at least 10 simultaneous assets; MAD > 1e-12.
- Transform: tanh with fixed unit scale, then L1 normalization.
- Alpha gross: 0.20 fixed.
- Cost gate: severe first using existing canonical execution model.
- Selection: chronological train only with existing temporal-fold `stable_train` gate.
- Missing archives remain missing; no filling/interpolation.
- Single hypothesis, no parameter grid, no sign flip, no rescue, no retuning after seeing PnL.
- Holdout MUST NOT be listed, downloaded, parsed, inspected, or optimized.
- V16 Frozen and V99 Frozen MUST remain byte-identical.

## Decision
PASS only if the existing `stable_train` train/fold gate passes. PASS freezes this exact specification for supersevere/regime/benchmark/reproducibility gates before any untouched holdout access. FAIL is permanent for this specification.