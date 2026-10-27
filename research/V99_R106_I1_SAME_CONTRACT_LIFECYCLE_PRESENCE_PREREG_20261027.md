# V99 I1 — ex ante contract-continuity source screen (2026-10-27 17:45 BRT)

Status: SOURCE_ONLY/HOLD. This is a necessary-source screen, NOT an economic backtest, execution, or certification.

## Failure mode discovered before implementation
The current 661-day gate counts 180/180 *synthetic* BTC+ETH asset-weeks when each day contains a **different option contract** with expiry equal to that day plus 28 days. It explicitly labels this weak market presence, but a naive downstream user could treat it as a complete lifecycle. A 28–35d put vertical requires **the same two specific puts with the same expiry** to be observable from entry through pre-expiry marks. The current daily-any-contract presence cannot establish that.

## Fixed algorithm (no tuning or sealed dates)
- Only the existing 90 Monday entry dates and BTC/ETH, in [2021-12-09, 2023-10-01). No validation or final holdout.
- For each Monday and each expiry in [Monday+28d, Monday+35d] with expiry < 2023-10-01, track exact put symbols from that Monday through every UTC day strictly BEFORE expiry. Require valid, original-hash-bound, five-minute-fresh two-sided positive quotes and positive sizes each day, in original local-arrival order.
- A candidate expiry passes this **necessary** continuity screen if at least two distinct put symbols of the same asset and expiry have all pre-expiry days. Do not assume the pair meets 0.9/0.8 moneyness, synchronized executable quote, native fees, margin, exit, or settlement. This is NOT a certified complete lifecycle.
- Report per-asset-week boolean and aggregate count independently of the existing weak 180/180 metric. Independent oracle replays original CSV bytes, not primary output alone. A forged report must fail.
- Negative control: daily new synthetic contracts yield 180/180 weak presence but **0/180 same-contract pair continuity**. Positive control: inject two stable puts for one asset/expiry over every required pre-expiry day and require exactly 1/180 continuity, while keeping fixture/quarantine.
- No promotion, no PnL, no source entitlement claim, no orders; never alter Frozen, paper, champion, or sealed periods. Original vendor 2021–2023 tape and historical native terms remain mandatory.

Decision gate: only if source files arrive may this screen establish necessary per-contract continuity; it cannot unlock economic TRAIN or validation by itself.
