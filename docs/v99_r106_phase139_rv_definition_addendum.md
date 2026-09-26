# V99 R106 Phase139 — RV24 Definition Addendum

Status: **PREREGISTERED CLARIFICATION / BEFORE ANY PHASE139 PNL**

The Phase139 preregistration froze a 24-completed-hour realized-volatility feature but did not spell out the algebraic RV estimator. Before implementing or observing any Phase139 PnL, freeze the conventional unannualized estimator below for both venues:

`RV24_t = sqrt(sum_{i=t-23..t} r_i^2)`

where `r_i = log(close_i / close_{i-1})` and all 24 returns must be available. No demeaning, annualization, winsorization, thresholding, alternative window, or estimator search is permitted.

Then exactly as already preregistered:

`vol_gap_t = RV24_OKX_t - RV24_Binance_t`

Normalize `vol_gap` with the exact same-window 168h median/MAD, cross-sectionally demean each hour, freeze direction as reversion, and shift the complete final score by exactly `t-1` before execution. Missing required venue observations remain unavailable; no forward/back fill.

This addendum resolves implementation ambiguity only. It does not alter the hypothesis, direction, universe, windows, gate sequence, costs, folds, holdout discipline, or rejection rule, and was committed before any Phase139 PnL was observed.
