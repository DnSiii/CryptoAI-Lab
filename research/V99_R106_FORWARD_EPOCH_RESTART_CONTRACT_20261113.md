# R106 forward epoch restart — fail-closed implementation contract (2026-11-13)

Status: BLOCKED; research-only; no real orders; no candidate promotion.

## Verified evidence
GitHub Actions 43406433471, job 131821788935, commit 49cd20fa9e2b2ac717b17a49c007e24163ab2c52 failed in the **preflight**, before any paper cycle. Its report returned `NEW_VERSIONED_EPOCH_REQUIRED`, `current_epoch_guard_can_pass_any_candidate=false`, and old ledger SHA-256 `f188c4d95761c4ddf4719f4d86bfab0faa54a65f79d576f42ce3cc4f09e17089`. F1/F3 had capped operation ledgers; F1/F12/F3/F7/R98 had backtest references crossing the paper boundary. Do not retry old-epoch append or bypass this guard.

Separately, Actions 43409174429 succeeded for the **frozen public-data paper**; that does not demonstrate that the R106 five-variant forward epoch or the publicly served dashboard is economically current.

## New epoch implementation requirements
1. Read old `paper-results` as immutable input; record the old SHA-256, commit, boundary and all five variant IDs. Never rewrite, truncate, extend or rebase old operation histories. New namespace, new epoch ID and new artifact paths, with explicit link to immutable predecessor.
2. Establish a strictly future UTC closed-candle start **after** the last historical reference for every variant. No old backtest/training rows may be copied as new forward decisions. If no common causal boundary is possible, refuse initialization.
3. Require raw first-party market and execution/funding provenance for each new decision: source, capture time, market event time, instrument, units, quantity, price, fee currency/amount, settled funding, raw-byte hash, and deterministic transformations. Missing original economic receipts means `RESEARCH_ONLY / ECONOMICS_UNVERIFIED`, not a validated fill or realized PnL.
4. Keep original paper verifier, frozen configurations, V16/V99 Frozen, published history and train/validation/holdout untouched. No real order capability. Do not invent historical trades to bridge the epoch gap.
5. Before any publication, independently check original-prefix immutability; non-overlapping boundaries; strictly increasing event times; duplicate and missing-hour handling; deterministic recomputation of notional, fees, funding and portfolio capital; timestamp provenance; source freshness; and explicit fail-closed stale/research-only status on the public page.
6. CI must demonstrate both rejection of the old epoch and acceptance of a *separate* future epoch using real receipts. Synthetic fixtures may test failure modes but cannot qualify economic provenance or strategy performance.
7. Verify the **served** GitHub Pages data payload, timestamps and visible stale warning separately from GitHub Actions success. Publish research platform independently of any superior-engine claim.

## Research gate
D1 and C1 remain rejected. I1 remains blocked pending 658/661 missing licensed original Deribit option-history days, or an independently sourced complete original dataset with verified licensing. Any distinct architecture must be preregistered and pass five chronological TRAIN folds with severe/supersevere costs and independent accounting before sealed validation; never inspect final holdout for tuning.

Next engineering action: implement a new versioned forward-epoch writer and its immutable-prefix oracle, wire to a dedicated workflow, then run Actions and inspect generated artifacts and served page. This document is an implementation contract, not evidence that those actions have completed.
