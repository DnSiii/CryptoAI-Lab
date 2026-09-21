# V99 R106 Phase99 — top-trader vs crowd positioning spread (TRAIN ONLY)

## Scientific question
Does the cross-sectional spread between top-trader account positioning and the broad account population contain causal continuation alpha that is distinct from absolute positioning levels and from Phase97's top-trader size-vs-headcount divergence?

## Precommitment (before any Phase99 PnL)
- Source: official Binance USD-M daily metrics archives, train dates only.
- Fields: `count_toptrader_long_short_ratio` and `count_long_short_ratio`.
- Signal at timestamp t: `spread = log(count_toptrader_long_short_ratio) - log(count_long_short_ratio)`; shift the complete spread by one hour (`t-1`) before any portfolio use.
- Cross-section: at each timestamp, subtract simultaneous median and divide by simultaneous MAD; require >=10 assets and MAD > 1e-12.
- Mapping: `raw = tanh(z_spread)`. Positive means top traders are relatively more long than the broad crowd; fixed hypothesis is continuation in that direction.
- Portfolio: L1 normalize raw signal; fixed alpha gross = 0.20.
- Costs: severe first. No grid, no threshold search, no sign flip, no rescue, no post-result retuning.
- Selection: chronological train only through the existing Phase63 train_end. Four temporal folds and robust mean excluding top 1% hours use the existing diagnostic contract.
- Missing archives are not filled. Every consumed ZIP must pass official SHA256 and internal CRC checks.
- Holdout must not be listed, downloaded, parsed, inspected, or used for selection.
- V16 Frozen and V99 Frozen must remain byte-identical.

## Gate
PASS only if the existing `stable_train` diagnostic passes. On PASS, freeze this exact specification and proceed to supersevere, regime matrix, benchmark envelope and reproducibility before any untouched holdout gate. On FAIL, permanently reject Phase99 as specified and do not reverse/tune it from observed PnL.
