# Phase195-BM — Historical/forward separation, 2026-10-10 (research only)

**Decision: DATA_ONLY/HOLD.** No promotion, publication, live orders, holdout access, or Frozen modification. The public champion remains unchanged.

## Independent evidence (two archived research artifacts)
- Published/prior archive: local `research_prior.zip` (2026-10-10 01:06 UTC archive timestamp); candidate: official run 38032784420 (2026-10-10 07:08 UTC archive timestamp). These are **workflow artifacts**, not authenticated exchange receipts.
- Shared paper boundary: **2026-09-16T13:00:00Z**. Five variants each have **2,451 pre-boundary historical daily points**.
- Prior artifact: **24 post-boundary points mislabeled backtest** per variant; candidate: **25** per variant. These belong in forward research, not historical backtest.
- Pre-boundary historical changes on comparable dates: R98 0, F1 **55** (first 2026-07-24T02:00Z), F3 **94** (first 2026-06-15T02:00Z), F7 0, F12 0. The F1/F3 historical prefixes are not immutable.
- Latest V99 research paper workflow run 38056208391 failed its fail-closed gate: 50 mislabeled points per variant counted across published and candidate references; F1/F3 452 published hours rewritten each; capped operations and historical backtest mismatch. No paper-results publication.
- Three official V15 archives 38043966853, 38044661910, 38045334304: 129 dynamic assets have eligibility earlier than the conservative first-safe hour; 12 symbols are repeatedly reported new; 191 observed dynamic adjustments, 0 premature within those **capped observations**. This does not certify earlier as-of discovery.

## Changes
- New `scripts/v99_phase195bm_historical_partition.py`: strict UTC, chronological, finite positive historical equity, fail-closed read-only reference comparison; **always** returns DATA_ONLY/HOLD.
- Research paper candidate assembly now clips equity before the shared paper boundary and separately rejects any historical row at or after the boundary. This only fixes candidate display classification; it does **not** repair the published baseline, certify train-only selection, or permit publication.
- 11 synthetic adversarial tests and isolated CI. No changes to V16 Frozen, V99 Frozen, main, paper-results, gh-pages, or dashboard.

## Preregistered next experiment (not executed)
Before any PnL evaluation: authenticate immutable source-time OHLC/funding/first-seen receipts; pin code SHA, market input hashes, exact train windows, universe, transaction costs, temporal folds, benchmark envelope, and regime matrix. Then run a *single preregistered* four-arm paired causal replay on train-only folds: (A) baseline, (B) funding-only correction, (C) point-in-time universe-only, (D) both. No tuning on the untouched holdout, paper history, or the 55/94 revised historical points. Require severe/supersevere cost gates and concentration/tail audits. Reject on any provenance or parity failure; retain champion until fully validated.
