# V99 R106 Phase66 — positioning dispersion preregistration

## Decision context
Phase65 crowd-positioning level contrarian was rejected train-only (0/4 healthy folds). No sign flip, threshold, smoothing, or field substitution is permitted as a rescue of Phase65.

## Single orthogonal hypothesis
Test whether **cross-sectional disagreement between native account-count positioning and native top-trader position positioning** contains an independent relative-value signal. The economic hypothesis is that a large divergence between broad account crowding and top-trader position crowding identifies asymmetric positioning pressure not represented by either level alone.

## Locked transform
For each asset/hour, using only native Binance USD-M metrics observations available before the decision bar:

`dispersion = log(top_long_short_position_ratio / count_long_short_ratio).shift(1)`

Both ratios must be finite and strictly positive at the same native timestamp. Otherwise the observation is missing. No imputation, forward-fill, proxy, alternate field, sign flip, smoothing, clipping, threshold sweep, or parameter grid is allowed. Cross-sectional portfolio construction reuses the already-audited Phase31 weighting function unchanged. Alpha gross is fixed at 0.20.

## Data/integrity contract
Source is the already-audited Binance USD-M daily metrics archive universe from Phase63. Every consumed ZIP must pass published SHA256 and ZIP CRC checks. Only dates through Phase63 `train_end` may be requested or parsed. Missing archives and blank/nonfinite observations remain missing.

## Selection/gates
Selection is chronological TRAIN-ONLY. Holdout must not be listed, requested, parsed, scored, or inspected. Preserve causal t-1, the existing four temporal folds, severe cost model, existing mapper/guard, reproducibility, frozen-asset guards, and anti-overfit rules. Promotion requires the existing `stable_train` gate (>=3/4 healthy folds and all existing robust diagnostics). If rejected, Phase66 is dead: no rescue retuning. If passed, freeze the exact specification before any untouched-holdout evaluation.

V16 Frozen and V99 Frozen must remain byte-for-byte untouched.
