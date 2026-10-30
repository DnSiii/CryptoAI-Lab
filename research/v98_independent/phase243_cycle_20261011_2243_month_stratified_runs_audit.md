# V98 Independent — Phase243 monthly zero-state runs audit (2026-10-11 22:43 BRT)

DATA ONLY / NO ALPHA. Branch: `research/v98-independent-zero`. Scope: V98 Independent frozen funding series, 2023-01 through 2025-12 inclusive; untouched 2026+ holdout; no V16/V99 data, workflows, reports, paper or state.

## Verified inputs and source provenance

Read the five frozen Phase206 funding CSVs directly from the requested GitHub branch. All contain 3,288 aligned 8h training settlements (36 calendar months). The BNB CSV Git blob is `6b46a2a911d85079f3ce4ec5bc8b1791febd397a`. Git SHA and internal source consistency are **not** independent publisher authentication. BNB contains 1,800 exact zero funding rates; BTC/ETH/XRP/SOL have zero exact zeros in the same 2023–2025 window.

## Independent month-stratified clustering diagnostic

For each calendar month separately, let `n1` be the number of zero rates, `n0` nonzero rates, and `T` the observed number of zero/nonzero transitions between adjacent 8h settlements. Under a **purely descriptive** uniform permutation of that month's fixed zero count, `E[T] = 2*n0*n1/(n0+n1)` and `Var(T) = 2*n0*n1*(2*n0*n1-n)/(n*n*(n-1))`, with `n=n0+n1`.

Summed across the 36 months, BNB exhibits **725 observed within-month transitions** versus **1319.4 expected** under independent monthly shuffles (ratio ~0.550). **27 of 36 months** have a negative descriptive permutation-reference z-score below -3. The most extreme is 2024-06: 70 zeros in 90 settlements, only 3 transitions versus 31.11 shuffle-reference transitions (z≈-8.66). 2024-07 has 84/93 zeros, 7 observed transitions versus 16.26 expected (z≈-5.64).

These numbers show substantial temporal persistence **even after preserving each month's zero prevalence**. The permutation reference is not a realistic independent-trial market null: funding has serial dependence, policy/regime persistence, cross-month spillover and potential source-format mechanisms. No p-value is interpreted as a trading edge, proof of source defect, causal effect or independently authenticated market observation. This is a source-integrity diagnostic only; do not tune a zero-run trading rule.

## Operational gate, reproducibility and next action

The existing V98 source-acquisition workflow (latest recorded run 38053620316, failed 2026-10-10) still does not invoke the committed independent XRP daily 1h/1m capture script before its 185-archive source gate. A targeted update of `phase243_source_acquisition.py` was attempted in this cycle and **blocked by tool safety checks**. No workflow launched or source repaired. The unchanged workflow preserves failed monthly quarantine but cannot yet collect orthogonal daily witnesses.

Local synthetic validation: 83 distinct tests across XRP source capture, full-day minute adjudication, preregistered pairwise tolerance, pre-grid capture sequencing and the new month-stratified runs validator. Four deterministic modes (PYTHONHASHSEED=1/777 × normal/-O) passed **332/332 test executions**. The new validator was not published in this commit; it remains in the cycle's local evidence package. No historical backtest was executed.

Decision remains **Phase240 REJECT_FAMILY_NO_RESCUE; Phase243 BLOCKED_SOURCE; champion NONE**. Preserve original funding/price sources, 2026+ holdout, causal chronological folds, all economic costs/stress/tail gates, and untouched V16/V99 state. Next: publish a narrowly scoped V98 source-capture integration through an authorized path, obtain original XRP daily 1h/1m and Binance sidecars, compare all 24 hours/1440 minutes, independently authenticate BNB funding provenance, then reassess the data-only gate. No promotion until all economic and anti-overfit gates are met.

## Independent XRP exact-decimal physical bounds (same cycle)

Reopened **only** the preserved V98 monthly original `XRPUSDT-1h-2023-11.zip` (720 hourly rows, archive SHA256 `29b7a4a3b9360f7b3be131af6b1fd619f18e7344eea99b5c964e955e667027a7`) from the previous V98-only evidence package. At 2023-11-14 11:00 UTC (row 323), candle high=0.6556, base volume=62,032,915.1, quote volume=51,332,637.23413, taker-buy base=33,020,819, taker-buy quote=21,496,999.26064 (USDT units for quote).

Two **independent physical upper bounds** were checked using exact Decimal arithmetic: total quote <= base*high = **40,668,779.13956** (observed excess **10,663,858.09457 USDT**), and seller residual quote <= taker-buy quote + (total base - taker-buy base)*high = **40,517,329.46380** (observed excess **10,815,307.77033 USDT**). The seller-residual constraint is **151,449.67576 USDT tighter**. The implied seller VWAP is ~1.028386, versus the recorded candle high 0.6556. The taker-buy VWAP remains physically plausible (~0.651014). Both independent checks flag **exactly one of 720 rows**, and the taker-buy bound flags zero. This narrows the defect mechanism but cannot determine a correct replacement value.

Importantly, the corrupted hour is only **98th-largest quote volume of 720 hours**, so an ordinary large-volume outlier screen would miss this physically impossible record. These are arithmetic integrity findings, not a new trading hypothesis or proof of what the original exchange recorded. The three orthogonal daily sources are still missing; no repair or source selection is authorized.
