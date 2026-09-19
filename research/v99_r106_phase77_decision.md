# V99 R106 Phase77 — decision

Status: **REJECTED permanently on train-only evidence**.

Phase77 tested the preregistered one-hour change in top-trader position-vs-account disagreement, `diff(log(sum_toptrader_long_short_ratio/count_toptrader_long_short_ratio),1).shift(1)`, with the frozen Phase31 cross-sectional mapper, gross 0.20 and severe costs.

Observed train-only result through 2024-01-18: ROI -16.04%, profit factor 0.9302, max drawdown 19.01%, robust mean excluding top 1% -4.684e-05, 4 valid temporal folds and 0 healthy folds. The candidate therefore fails the existing Phase47 `stable_train` gate.

Decision is final for this specification: no sign flip, horizon/level substitution, smoothing, threshold search or regime rescue. The untouched holdout was not listed, parsed or inspected. V16 Frozen and V99 Frozen remain immutable.

Next independent preregistered test: Phase78 taker-flow change dynamics.
