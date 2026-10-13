# V99 R106 Phase195-FN — causal receipt gate and official continuity (2026-10-13)

**Decision: DATA_ONLY/HOLD. No promotion.** Research branch only; V16 Frozen, V99 Frozen, holdout and public champions unchanged.

## Official immutable evidence
Compared GitHub Actions paper runs 38455868784 and 38456754324, each completed successfully, with independently downloaded artifact ZIP SHA-256:
- 38455868784: `3ccefe28e3098976b5b9cd72dbd6d2fd61b81c0db61737e471225f3b21ec4b58`
- 38456754324: `15c6f1ff980729b5c3e00430f5a1f590744efad1b31f095acfac6812908c2d11`

All **8 paper equity histories** are byte-equivalent as JSON sequences; no new hourly record and no changed non-curve ledger fields in this pair. Last official close 2026-10-13 18:00 UTC. This confirms only this transition, not independent market-data provenance.

## Forward-eligible, not forward-verified
At migration boundary 2026-10-13 16:00 UTC through 18:00 UTC, **two prospective-eligible hours** are present: V99 `-0.0135683%`, V16 `-0.0129297%` (equity-ratio basis). Hourly capital deltas V99 +R$12.42 then -R$13.57; V16 +R$12.56 then -R$13.67. Difference V99 minus V16 **-0.0006386 percentage points**. Neither run has independent exchange-as-of receipts, and V99 has **0/885** rows with complete gross/fee/funding/net attribution. Do not interpret these as independently validated forward evidence or use for candidate selection.

## Structural first-seen defect and conservative research gate
The dynamic universe contains 176 symbols; **128 dynamic symbols** have `eligible_after_timestamp` earlier than the first hourly close at/after `discovered_at_utc` (127 prior plus ARCUSDT). ARCUSDT discovered 18:46:39.622859 UTC, configured eligible 17:00 UTC; first safe target close 19:00 UTC. This is **eligibility metadata lookahead risk**, not proof of executed lookahead. ARCUSDT appears in V15's execution checkpoint but not V16/V99 assets or decision records in this artifact.

A versioned research-only receipt gate was implemented and tested locally. It requires strict UTC, causal first-seen close, receipt request/response/exchange-as-of ordering, a payload digest, and external receipt authentication; missing provenance zeroes research dynamic targets. The tool cannot itself authenticate an asserted receipt flag: an independently preserved external immutable source must establish it. **No retroactive rewrite, no production/frozen modification.**

## Paired-tail diagnostics (descriptive only)
884 paired hourly returns; V99 exceeds V16 on 435 hours and trails on 449. V99 worst 5 hours: 2026-10-05 14:00 UTC -2.6908%, 2026-09-23 15:00 -2.6380%, 2026-09-20 02:00 -2.3817%, 2026-09-13 22:00 -2.3532%, 2026-09-23 14:00 -2.2104%. Window contains retrospective/recovered hours; no model-selection inference is permitted.

## Preregistered next work
1. Obtain independently timestamped Binance exchange-as-of request/response evidence, content hashes and arrival-time proof for first-seen symbols, without retroactive fabrication.
2. Run separate, versioned causal research replays: legacy baseline, funding PIT, discovery PIT, both; strict t-1, chronological train-only folds, severe/supersevere costs, 3x2 regimes, benchmark envelope, untouched holdout.
3. Reconstruct research-only V99 gross/fees/funding/transfers/net shadow accounting and reconcile exact frozen equity, failing closed if inputs are absent.
4. Keep the five-variant R98/R106 publication guard intact until 53 boundary points and 568/452 historical rewrites are reconciled. Do not relabel or overwrite published paper.
5. Update dashboard only on independently validated material improvement, keeping separate historical, holdout, forward and research statuses.

**No promotion; no Frozen or dashboard changes.**
