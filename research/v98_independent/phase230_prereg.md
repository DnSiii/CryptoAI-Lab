# V98 Independent — Phase230 preregistration

Status: **PREREGISTERED BEFORE RESULTS**.

## Hypothesis
Test a scientifically distinct cross-sectional **idiosyncratic momentum** family: after removing the contemporaneously observable crypto-market component from each asset's trailing return, assets with persistently positive residual momentum may continue to outperform assets with negative residual momentum. This differs from Phase226/227 residual reversal and from Phase228 breakout/Phase229 calendar periodicity: the signal is ranked cross-sectionally on lagged multi-hour residual momentum and is market-neutral by construction.

## Frozen information set / execution
- Decision timestamp: open(t).
- Every feature must use prices ending no later than open(t-1); no bar t return/high/low/close may enter the signal.
- Market factor at each historical hour is the equal-weight return of available assets at that same historical hour only; residuals are asset return minus that historical cross-sectional factor. No future beta/factor estimation.
- Signal is the trailing sum of residual returns over a frozen lookback, shifted so the newest contributing return ends at open(t-1).
- At open(t), long the strongest residual-momentum asset(s) and short the weakest, equal gross on both sides; gross exposure <= 1 and net target 0 when both sides exist. No ex-post asset deletion.
- Hold for frozen h hours with deterministic overlapping sleeve accounting. No same-bar feature/execution leakage.

## Frozen grid — exactly 8 specs
1. `idio_mom_lb24_k1_h4`
2. `idio_mom_lb24_k1_h8`
3. `idio_mom_lb72_k1_h4`
4. `idio_mom_lb72_k1_h8`
5. `idio_mom_lb168_k1_h4`
6. `idio_mom_lb168_k1_h8`
7. `idio_mom_lb72_k2_h4`
8. `idio_mom_lb168_k2_h8`

`k1` means long top-1 / short bottom-1; `k2` means top-2 / bottom-2. Ties must be broken deterministically by symbol.

## Frozen evaluation
- Chronological folds: calendar 2023, 2024, 2025 only.
- Holdout: all timestamps >= 2026-01-01 remain untouched.
- Trading costs: base 7 bp, severe 14 bp, supersevere 28 bp applied consistently to turnover/entries-exits under the repository's V98 accounting convention.
- Funding: point-in-time only, aligned to actual held side/exposure; no future funding knowledge.
- Required outputs per spec/year/stress: return, max drawdown, Profit Factor, payoff, win rate, positive days, trade count, tails p01/p05/p50/p95/p99, worst/best trade, asset PnL contribution/max concentration, funding contribution, and bear/bull/sideways regime metrics.
- Determinism: two independent executions must produce byte-identical normalized payloads and matching SHA256.

## Gate / anti-overfit
A spec may survive only under the pre-existing V98 decision-grade mechanical gate, without weakening thresholds after observation. Severe/supersevere must be inspected, and robustness cannot be rescued by dropping an asset/regime/year. If zero specs survive, decision is `REJECT_FAMILY_NO_RESCUE` and Phase230 closes. If any survives, proceed to independent causality/accounting audit before any promotion. No 2026+ data may be opened for selection or tuning.
