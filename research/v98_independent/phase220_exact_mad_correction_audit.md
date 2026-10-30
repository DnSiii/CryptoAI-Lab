# V98 Independent Phase220 — exact-MAD correction audit

Date: 2026-10-03

## Decision boundary

The first Phase220 output (workflow run 37091219271; deterministic file SHA256 `942cd6ac152ef69ae70e238539d31fbcefe21737fcd9b3172bd72d038d3b94a0`) is **non-decision-grade** and MUST NOT be used for promotion, rejection, parameter selection, rescue, or tuning. It was generated after the preregistered family was frozen but before the implementation defect below was corrected.

## Defect

The initial implementation computed:

`median(|x_t - rolling_median_t|)` through a second rolling operation over already-centered observations.

That is not the preregistered same-window median absolute deviation:

`MAD_t = median_{i in window_t}(|x_i - median(window_t)|)`.

The distinction is material because each absolute deviation must be centered on the median of the *same N-event window* before taking that window's median.

## Correction

Commit `5925598d3e08ef633b75ad83c52c947736b0a84a` replaces the estimator with an exact rolling-window function:

`rolling(N).apply(lambda x: median(abs(x - median(x))))`.

No frozen research degree of freedom changed: universe, N in {21,63}, S in {1.0,1.5}, holds {4h,8h}, long/short direction, 50/50 weights, chronological folds, cost levels, funding treatment, or gate remain unchanged.

Commit `94cb31adba0ad1bb85b9a40a9eab4c47657d1056` strengthens the workflow invariant so future Phase220 decision-grade runs must explicitly contain the exact same-window MAD implementation and report `mad_definition=exact_same_window_median_absolute_deviation`.

## Anti-overfit / holdout status

No 2026+ data were opened. The correction was triggered by a formula audit, not by Phase220 performance. The invalid first result cannot influence the frozen grid or the corrected run's decision. V99/V16 state is outside this audit and must remain untouched.

## Required decision-grade evidence

A corrected Phase220 result is eligible for evaluation only after: training-only rebuild and `<2026` firewall; exact-MAD invariant; two deterministic executions with identical SHA; monotonic base/severe/supersevere stress; all 8 frozen specs across 2023/2024/2025; complete MDD, PF, payoff, win rate, positive days, tails, concentration, funding contribution, and regime diagnostics. Mechanical promotion/rejection follows only after those checks.