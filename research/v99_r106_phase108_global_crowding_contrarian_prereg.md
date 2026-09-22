# V99 R106 Phase108 — global-account crowding contrarian alpha (PRE-REGISTERED)

## Status
Pre-registered before any Phase108 PnL is computed. Phase107 is permanently rejected; no Phase107 sign flip or rescue is permitted.

## Hypothesis
The Binance USD-M `global_long_short_account_ratio` measures broad account-count positioning rather than top-trader size-weighted conviction. Extreme cross-sectional broad-account long crowding is hypothesized to be a contrarian signal: assets with unusually high broad-account long/short ratios receive negative target direction, and unusually low ratios receive positive target direction.

## Frozen transform
1. Use only archives already admitted by the Phase63 train-only metrics data audit; do not list, request, parse, or infer holdout archives.
2. For each symbol/hour, take `log(global_long_short_account_ratio)` when finite and strictly positive.
3. At each timestamp compute cross-sectional median/MAD robust z-score, requiring >=10 simultaneous assets and MAD > 1e-12.
4. Apply a fixed negative sign (contrarian direction) and `tanh`; shift the whole alpha by exactly t-1 before trading.
5. L1-normalize cross-section and run at fixed alpha gross 0.20.
6. First decision gate uses the canonical severe cost model and the existing chronological train-only temporal-fold diagnostic.

## Anti-overfit constraints
Single hypothesis, no parameter grid, no threshold search, no post-result sign flip, no rescue, no retuning. Missing archives remain missing. Selection is chronological train-only. V16 Frozen and V99 Frozen are read-only and hash-guarded. Untouched holdout is prohibited until an exact candidate is frozen after all downstream train/validation gates.

## Decision
PASS only if the existing `stable_train` gate passes unchanged. PASS freezes this exact specification for supersevere costs, regime matrix, benchmark envelope and reproducibility before any holdout access. FAIL is permanent and Phase108 ends without modification.
