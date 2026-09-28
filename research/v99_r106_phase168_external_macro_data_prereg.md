# V99 R106 Phase168 — External Macro DATA-only preregistration

Status: PREREGISTERED DATA ONLY. BEFORE ANY Phase168 PnL.

## Motivation
Phase167 Coinbase cross-venue OHLC is rejected under its frozen source contract because XRP-USD has only ~24.19% TRAIN hourly coverage, while BTC/ETH/SOL/DOGE are ~99.97%+. More importantly, cross-venue OHLC is already a closed research family (Phases149–157), so no alpha rescue or asset dropping is permitted.

Phase168 moves to a genuinely orthogonal information family: external macro/risk-market state, not another crypto venue or derivative positioning transform.

## Frozen DATA-only contract
- TRAIN only: 2021-12-01T00:00:00Z <= t < 2024-01-18T00:00:00Z.
- No holdout rows may be fetched for feature construction or selection.
- No strategy PnL, returns-conditioned threshold selection, asset selection, sign choice, or parameter search.
- V16 Frozen and V99 Frozen are read-only and must remain untouched.
- Candidate public series to audit as fixed panel: FRED DFF (effective federal funds rate), DGS2 (2Y Treasury), DGS10 (10Y Treasury), DTWEXBGS (broad USD index), VIXCLS (VIX close).
- Raw native daily observations only; missing markers are preserved as missing. No post-observation dropping of a weak series to manufacture PASS.
- Required per-series checks: successful retrieval, parseable dates/values, strictly increasing unique dates after canonicalization, no observations outside TRAIN, native observation count, finite-value coverage on expected business-day grid, longest missing run.
- PASS_DATA_ONLY requires each frozen series >= 90% finite business-day coverage over TRAIN and no unexplained longest missing run > 10 business days. Known calendar holidays/weekends are handled only by the business-day denominator; no forward-fill is performed in this DATA gate.
- Evidence report must explicitly state pnl_computed=false, holdout_rows_used_for_feature_construction=0, holdout_rows_used_for_selection=0, frozen_assets_untouched={v16:true,v99_frozen:true}.

## If and only if PASS_DATA_ONLY
A later phase may preregister one causal t-1 macro mechanism before any PnL. Any such alpha phase must retain chronological train-only selection, temporal folds, severe/supersevere costs, regime matrix, benchmark envelope, reproducibility and anti-overfit gates.

## Failure policy
FAIL_DATA_ONLY closes this exact frozen macro panel. Do not rescue by dropping a failed series, changing coverage thresholds, inspecting holdout, or mining PnL. Move to a scientifically distinct source/mechanism instead.
