# V99 R106 Phase124 — TRADE-SIZE DISPERSION / PARTICIPATION CONCENTRATION preregistration

Status: PREREGISTERED BEFORE ANY PHASE124 PnL.

## Motivation
Phases121-123 rejected three standalone aggressor-direction formulations under severe costs. Phase124 therefore leaves aggressor direction entirely and tests a distinct microstructure mechanism: whether unusually concentrated trade-size participation identifies persistent cross-sectional activity/price-pressure states. The signal uses unsigned aggTrade size dispersion, not buyer-vs-seller sign, run direction, taker imbalance, OI, funding, premium, positioning, or bookDepth.

## Source and admissibility
- Official Binance USD-M daily `aggTrades` archives only, with official CHECKSUM verification and ZIP CRC.
- Train observations strictly before `2024-01-18 00:00:00 UTC`; any parsed trade timestamp >= train end is a hard failure.
- Holdout market values must not be downloaded or parsed by the train gate.
- Missing archives remain missing; no future fill, interpolation, synthetic reconstruction, or third-party substitution.
- Universe must be selected without PnL/returns, using the already established resource/coverage rule and requiring >=8 executable symbols. No symbol substitution after PnL.

## Frozen single hypothesis
For each symbol/hour aggregate unsigned quote notional per aggTrade, `q_i = price_i * quantity_i`.

Define participation concentration as the Herfindahl share of trade notionals within the hour:

`HHI = sum(q_i^2) / sum(q_i)^2`, for hours with >=2 valid trades and positive total notional.

Use `C = log(HHI)` as the raw feature. At each hour, across the eligible executable cross-section, robust-standardize `C` using median/MAD with the canonical finite-value safeguards, winsorize only through the existing canonical robust transform if that harness already does so, then `tanh` to bounded score. No threshold/grid/search.

Direction is frozen as **continuation**: higher-than-cross-section lagged concentration receives positive target, lower concentration negative target. Center targets cross-sectionally, scale to fixed `L1 gross = 0.20`, and shift the entire target vector by exactly one hour (`t-1`) before return realization/execution.

No alternative sign, HHI variant, entropy/Gini substitution, rolling horizon, quantile threshold, gross, symbol count, or parameter search is permitted after observing Phase124 PnL. A failure permanently rejects this exact hypothesis.

## Evaluation contract
1. Causality/invariant checks before PnL: timestamp boundary, checksum/CRC, finite feature, exact target `t-1`, universe/executable intersection, no holdout parse, Frozen byte hashes.
2. Canonical R106 **severe-cost train-only** evaluation.
3. Existing chronological temporal-fold diagnostic; promotion requires the unchanged `stable_train` contract (>=3 valid and >=3 healthy folds plus all existing quality conditions).
4. Only a train PASS freezes this exact specification and permits **supersevere** costs, regime matrix, tails/concentration/pathology audit, benchmark envelope, and deterministic reproducibility checks.
5. Untouched holdout remains sealed until all required pre-holdout gates pass on the frozen exact candidate.
6. Any required-gate FAIL => permanent rejection, no repair/retuning/sign flip.

## Independence / anti-overfit note
This hypothesis was chosen from mechanism, not Phase124 returns: it tests *who dominates trade-size participation* rather than *which aggressor side dominates*. Phase121-123 results justify leaving the signed-flow family but do not determine Phase124's sign or parameters. The single continuation sign is frozen here before implementation/PnL.

V16 Frozen and V99 Frozen are immutable.