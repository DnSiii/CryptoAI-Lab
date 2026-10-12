# V99 Phase195-ED — 2026-10-12 — shadow settlement quarantine (DATA_ONLY/HOLD)

Scope: `research/v99-r106-native-all-regime-engine`; **no changes** to V16 Frozen, V99 Frozen, the untouched holdout, `paper-results`, or `gh-pages`. No champion promotion.

## New independent official-run evidence

Analyzed 46 distinct GitHub Actions candidate artifacts through run `38216741264` (latest comparable closed-hour boundary `2026-10-12T06:00:00Z`), including eight newly harvested runs `38209836674`, `38210748047`, `38211710248`, `38212654192`, `38213670612`, `38214637681`, `38215764555`, `38216741264`.

* Published baseline remained stable across 45 adjacent pairs; candidate histories had **one** eight-track financial rewrite pair, with no decision-prefix rewrites or boundary regressions.
* The durable published prefix is **not** equal to the recomputed candidate at `2026-10-01T16:00:00Z` for eight tracks. Thus **368 mismatch observations = 46 archives × 8 tracks**, representing **one distinct timestamp and one delta signature**, not 368 independent events.
* Funding source metadata: zero reported latest-event timestamp regressions and zero V13/V15 overlap disagreements. **152** stage-symbol-run observations lacked a same-stage REST receipt: **92** stale MKRUSDT and **60** same-run upstream-stage reuse observations. These are not independently authenticated source receipts.
* Descriptive paired forward-candidate window `2026-10-01T16:00:00Z` → `2026-10-12T06:00:00Z` (254 hourly returns): V99 ROI **-5.0703%**, max DD **7.9930%**; V16 ROI **-4.9653%**, max DD **7.9410%**. Neither is an accepted new forward-paper result.

## Scientifically distinct shadow policy (not a trading strategy)

A deterministic offline gate was tested against runner-reported funding metadata only. The existing generic 12-hour staleness rule would have admitted **46/46** snapshots. A BTC/ETH expected-settlement watermark (using an **unverified** 8-hour working cadence) would have admitted **41/46**, quarantining **five** snapshots whose most recent reported BTC/ETH funding event was older than the expected `2026-10-12T00:00:00Z` settlement. First subsequent **observed** ready candidate: `2026-10-12T02:11:18Z`. The one observed eight-track candidate rewrite transition had a watermark-blocked before-snapshot and watermark-ready after-snapshot. **This is an observational association, not proof the gate prevents financial revisions.** A trusted contemporaneous receipt policy would admit **zero** archives because none carry independently authenticated first-seen evidence.

The local shadow-policy implementation passed 12 focused tests (including malformed chronology, missing core symbol, duplicate artifact, altered baseline, and candidate truncation); the combined local suite passed **121 tests**, with two expected duplicate-ZIP warnings and two pytest subtests. The implementation and evidence are held in the local Phase195-ED handoff package unless separately committed.

## Decision and preregistered next gate

**DATA_ONLY/HOLD. No promotion, no paper/dashboard overwrite.** Do not infer exchange settlement cadence from an observed schedule, a claimed REST URL, an HTTP Date header, or a later archive. Next: collect independent, immutable first-party raw funding response bodies, SHA256, independently trusted capture time, and per-symbol settlement cadence; require fail-closed t-1 availability. Then compare the preregistered four causal replay arms (legacy; funding-only; PIT-discovery-only; both) on the same chronological train-only selection, temporal folds, severe/supersevere costs, regime matrix and benchmark envelope, with holdout untouched until all prior gates pass. Reject any nonreproducible or overfit candidate. Never backfill or rewrite accepted forward paper.
