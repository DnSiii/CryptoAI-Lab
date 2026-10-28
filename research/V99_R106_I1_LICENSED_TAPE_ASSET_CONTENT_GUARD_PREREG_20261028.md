# V99 I1 — original 661-day import: semantic asset/content guard (preregistered 2026-10-28 01:45 BRT)

## Observed defect and critical-path scope
The existing local licensed archive importer verifies 661 gzip files, venue, arrival clocks and hashes, but can accept a 661-day tape containing **only BTC**, **only ETH**, **futures instead of options**, or exclusively zero/crossed quotes as a seemingly complete BTC+ETH options inventory. This is a source-readiness false positive, not an alpha improvement. Correct only this importer and its direct negative controls; do not alter strategy, economics, validation, holdout, Frozen, paper, champion or order routes.

## Ex-ante acceptance rules (fixed before implementation)
For **each** of the 661 UTC arrival days, require at least one causally timestamped, two-sided, strictly positive-sized, uncrossed original Deribit **BTC put option** and **ETH put option** with parseable positive strike, expiry after that day and no later than 45 calendar days from that day. Parse original literal symbol `BTC|ETH-DDMMMYY-strike-P` (case-insensitive expiry month); reject malformed symbols, expired puts, calls, futures and zero/negative/crossed/nonfinite books as qualifying evidence. Nonqualifying rows may remain in the original source tape, but do not count. Fail the import atomically with a dated error if either asset lacks qualifying content. Record the per-day **qualifying source row counts** and a clear non-certification flag, never infer a full lifecycle, native lots, fills or vendor gap completeness from a row.

## Precommitted negative controls and expected outcome
1. A 661-day two-asset fixture still passes importer + independent lifecycle oracle; **0** certified lifecycles, **0** economic TRAIN, **NO PROMOTION**.
2. Remove ETH from one otherwise valid day: importer fails and does not write a manifest.
3. Replace BTC with a BTC perpetual/future or malformed/expired put on one day: importer fails, no manifest.
4. Replace ETH book with zero size or crossed quote: importer fails, no manifest.
5. Existing missing-day, corrupted gzip, noncausal clocks, overwrite and nonfixture-license-evidence controls must remain green.
6. Actual CI on research branch must explicitly reproduce missing **licensed** archive and report BLOCKED; synthetic tests do not count as historical market data.

## Decision rule
If software tests pass, mark **SOURCE_ONLY/HOLD — NO PROMOTION**. Still require lawful 2021-12-09..2023-09-30 BTC+ETH original Deribit option BBO/sizes with arrival timestamps, original dated fees/lot/margin/liquidation/delivery index and independent full 5-fold TRAIN economics. Sealed validation from 2023-10-01 and final holdout remain unopened.
