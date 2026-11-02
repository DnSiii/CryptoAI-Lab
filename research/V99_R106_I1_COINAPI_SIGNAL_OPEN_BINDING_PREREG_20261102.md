# V99 I1 — ex-ante signal / original OPEN source binding (2026-11-02)

Scope: TRAIN 2021-12-09 to 2023-10-01 only. This is a source-integrity correction to the already fixed I1 architecture, **not a new candidate, strategy retune, or economics**.

## Defect and fixed acceptance criteria

The CoinAPI full-entry original-book helper previously checked the quote inventory and price/clock of each native OPEN but did not bind the OPEN's `signal` to the corresponding independently reconstructed ex-ante signal. A caller could attach an otherwise matching original book to a `NO_PREMIUM` or `NO_30D_HISTORY` decision and still receive an original-book parity report. This must fail closed before any native accounting handoff.

1. Validate exactly 180 scheduled BTC/ETH decision rows, each with the immutable chronological fold and one of the three fixed signal labels: `POSITIVE_EX_ANTE_PREMIUM`, `NO_PREMIUM`, `NO_30D_HISTORY`.
2. For each OPEN in either severe or supersevere native journal, require its own explicit `signal` field to match the corresponding source row and to be `POSITIVE_EX_ANTE_PREMIUM`. Do not require both cost paths to OPEN: legitimate scenario-specific risk vetoes can differ.
3. Preserve original quote/clock/book equality and the source-size-is-not-native-lots distinction. Reject missing or forged signal labels and OPENs on nonpositive/no-history signals.
4. Synthetic regression tests must demonstrate a valid positive OPEN and rejection of both mismatched and nonpositive OPEN. CI must be inspected; no claim of original economic TRAIN or exchange-certified returns.
5. Never read validation >= 2023-10-01, final holdout, Frozen, paper, champion, or submit orders.

External blocker unchanged: licensed complete original 661-day option quote/size lifecycles and independently authenticated native fee tier, contract-size units, margin, index/delivery, and fills. This correction cannot replace those receipts.
