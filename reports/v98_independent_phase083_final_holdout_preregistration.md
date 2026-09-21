# V98 Independent Phase083 — one-shot final holdout pre-registration

## Gate authorization
Phase081 passed the complete training gate and was frozen before validation. Phase082 then passed its separately pre-registered validation gate on 2026-01-01 through 2026-07-31: return +18.9017%, daily PF 1.4151, max drawdown -9.7005%, severe +13.6633%, supersevere +5.8194%, no ruin. No validation rescue or parameter search was performed.

## Frozen candidate
Exactly the Phase081 28-day cross-sectional lagged channel-location spread: BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT/XRPUSDT; 672-hour lagged channel location; long highest channel location, short lowest; daily 00:00 UTC rebalance; gross 0.75; unchanged V98 cost/funding model. No parameter, direction, threshold, universe, exposure, timing, ranking, or cost-model changes are permitted.

Frozen training anchors: positions SHA256 `eac49cb65271d67640a4e856c96eb9398bc25681b7d336228736228fce4a2357`; Phase081 preregistration SHA256 `9fc1866df50f26219458ef857e41c3928ea42e21c0fb313489b3283ce7d2c4bf`. Frozen validation positions SHA256 `4271a9d78363b04a8e97f55bbb54cac7f9c06fa0035f0eea341e57b34cea49dd`.

## One-shot final holdout boundary
Open exactly once: 2026-08-01 00:00 UTC through 2026-09-15 23:00 UTC, matching the already-declared final_holdout_start/end in `config/v98_independent.json`. The holdout has not been used for training, validation, parameter selection, direction choice, rescue, or hypothesis selection. Data acquisition/build may occur only after this pre-registration and must prove coverage through the declared end before scoring.

## Frozen diagnostics and gate
Report total return, max drawdown, daily Profit Factor, payoff, win rate, positive days, monthly diagnostics, BASE/severe/supersevere, regimes, concentration/tails, asset contribution, activation/exposure, and reproducibility hashes.

Final PASS requires: total return > 0; daily PF > 1.02; max drawdown >= -35%; severe return > 0; supersevere return > 0; no ruin. Any failure => **REJECT_FINAL_HOLDOUT** with no rescue, retuning, direction flip, threshold search, or second holdout attempt. Complete PASS => **PROMOTE_V98_INDEPENDENT_FINAL**.

## Anti-overfit declaration
This is the single authorized final-holdout opening for Phase081. No V99 or V16 evidence may be used. No post-holdout parameter modification can convert a failure into a pass. The final decision is deterministic from the frozen gate above.
