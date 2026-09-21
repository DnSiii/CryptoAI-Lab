# V99 R106 Phase91 — cancellation before PnL

## Decision
Phase91 is **CANCELLED BEFORE BACKTEST / PnL INSPECTION**. This is not a scientific rejection and no sign or parameter was observed.

## Reason
The frozen Phase91 transform computes a per-timestamp robust score `(x - median) / MAD`, then converts that score to a simultaneous percentile rank and centers it at 0.5. For every timestamp with positive finite MAD, subtracting a common median and dividing by the same positive MAD is a strictly monotone transformation of `x`. Therefore its percentile ranks are exactly the percentile ranks of the lagged log-level itself (apart from degenerate all-tie/MAD=0 cases). The fixed mean-reverting direction and L1 normalization then make Phase91 economically identical to the already rejected Phase90 raw-level cross-sectional rank signal.

Running Phase91 would therefore duplicate Phase90 rather than test the distinct mechanism claimed in the preregistration. The duplication was identified from the specification/code algebra before any Phase91 runner, workflow, backtest, PnL, fold metric, or holdout access.

## Integrity
- Phase90 remains permanently rejected.
- Phase91 preregistration remains immutable as audit evidence.
- No Phase91 PnL was generated or inspected.
- Holdout remains untouched and unlisted/unparsed.
- V16 Frozen and V99 Frozen remain untouched.
- No sign inversion, threshold sweep, rescue, or retuning was performed.

## Next step
A genuinely distinct hypothesis must preserve cross-sectional *distance magnitude* instead of collapsing it back to rank. Phase92 is separately pre-registered before implementation/evaluation.
