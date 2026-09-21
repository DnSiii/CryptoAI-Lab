# V98 Independent — Phase066 validation preregistration

Status: **FROZEN BEFORE VALIDATION PNL**

## Candidate entering validation

Phase065 is frozen exactly as trained: 30-calendar-day BTC-residual cross-sectional momentum; BTCUSDT/ETHUSDT/BNBUSDT/XRPUSDT/SOLUSDT; four non-BTC assets ranked at each 00:00 UTC boundary using information through t-1; long highest residual and short lowest residual; gross 0.75 (0.375/0.375); daily rebalance; no threshold, horizon, inversion, asset deletion, volatility filter, regime gate, parameter search or rescue.

Training gate passed before this document was created. Phase065 training evidence is immutable for this validation decision.

## Chronology and data opening

Validation interval is frozen as 2026-01-01 00:00 UTC through 2026-07-31 23:00 UTC. Data may be reconstructed only through 2026-07 for this gate. The untouched final holdout remains 2026-08-01 through 2026-09-15 and MUST NOT be downloaded, inspected, scored, tuned, selected or compared during Phase066.

The 30-day formation window may use pre-validation history solely to form the first validation signal; no pre-validation PnL is included in validation metrics.

## Execution and robustness

Use the exact Phase065 implementation and the same V98 cost/funding conventions: BASE 0.0007 per side with 1.0/1.0 funding multipliers; severe 0.0012 with 1.25 debit/0.75 credit; supersevere 0.0020 with 1.75 debit/0.50 credit. No parameter may change after validation is opened.

Mandatory validation diagnostics: total return, CAGR, max drawdown, daily Profit Factor, payoff, win rate, positive/negative days, turnover, worst/best day, p01/p05/CVaR05; monthly chronological slices; regime analysis; asset contribution/concentration; top/bottom tails; exposure diagnostics; reproducibility hash; BASE/severe/supersevere.

## Frozen validation promotion gate

Phase065 may be frozen as a final-holdout candidate only if ALL are true under BASE:
- validation total return > 0
- validation daily Profit Factor > 1.02
- validation max drawdown > -35%
- no ruin, data-integrity or causality failure

Severe and supersevere are mandatory robustness reports but do not override BASE. Any BASE failure is **REJECT_VALIDATION_NO_RESCUE**. There is no validation-driven retuning, alternate horizon, inversion, filter, universe change or second validation attempt.

## Final holdout contract

Passing validation does NOT authorize parameter changes. If Phase066 passes, freeze the candidate and separately preregister a one-time final-holdout evaluation before opening any 2026-08-01+ observation. The final holdout may be opened once only for the frozen candidate.

## Isolation

V99 and V16 evidence, parameters, reports, branches, workflows and paper state are forbidden inputs to this decision. This document contains no validation or final-holdout PnL.