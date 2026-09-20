# V99 R106 Phase83 — decision

Status: **PERMANENT REJECT — TRAIN-ONLY**.

Phase83 tested the preregistered native top-account vs taker-flow divergence exactly as frozen: `log(count_toptrader_long_short_ratio / sum_taker_long_short_vol_ratio).shift(1)`, continuation, Phase31 cross-sectional weighting, alpha gross 0.20 and severe costs.

Observed train-only gate: ROI -19.3242%, profit factor 0.90857, max drawdown 19.9355%, robust mean without top 1% -4.3601e-05, 0/4 healthy temporal folds. `stable_train=false`.

Decision: reject permanently. No sign flip, horizon, weight, smoothing, threshold, alpha-gross or symbol rescue is authorized. Holdout was not parsed or inspected. V16 Frozen and V99 Frozen remain untouched.

Because Phase83 failed, the already-preregistered contingent Phase84 OI-confirmed taker-flow hypothesis is now authorized to run exactly as frozen in `research/v99_r106_phase84_oi_confirmed_takerflow_prereg.md`.