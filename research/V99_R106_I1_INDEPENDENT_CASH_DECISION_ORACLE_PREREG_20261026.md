# V99 I1 — independent cash-decision oracle integrity (preregistered 2026-10-26 23:xx BRT)

Research-only. Existing fixed-vertical independent oracle currently accepts **any** unchanged wallet as a verified CASH decision, including a forged CASH report when a positive signal has an eligible original-style fixture book. This is a false-independent-validation defect, not a trading edge.

## Fixed correction before code
- Independently enumerate and validate all candidate two-leg quotes using the immutable 28–35d, 90%/80% +/-2pp, <=5min venue/arrival age, <=1s pair skew, same asset/expiry/index, positive native depth and credit, exact native ID terms, and deterministic ordering. Do not import primary selection logic.
- For `CASH_NO_ELIGIBLE_SOURCE_OR_SIGNAL`, require negative/warmup signal OR independently prove no valid pair. A positive signal with a valid pair cannot be called independently verified cash.
- For `CASH_RISK_VETO`, independently calculate the fixed scenario entry costs, net credit, reserve, immediate exit liability plus scenario exit fees/slippage, and maintenance for an empty wallet. Verify the declared veto reason against an actual violated inequality. Unsupported pre-existing position risk cases must fail closed as **not independently certified**, not be silently accepted.
- For fixture OPEN, independently check candidate ranking, source clocks/IDs, modeled fee/slippage, wallet cash, reserve, and appended position. Reject forged decisions and mutated wallets.
- Add adversarial controls for forged CASH on a positive valid book, forged risk veto, stale/invalid candidate and correct severe/supersevere risk rejection. Run actual GitHub CI and original-source veto. No synthetic profit claim, no historical TRAIN or unsealing.
- Preserve all immutable Frozen/paper/champion records, sealed validation/holdout and no orders. SOURCE_ONLY/HOLD until full licensed 2021–2023 original BTC/ETH option lifecycle and native terms are independently attested.
