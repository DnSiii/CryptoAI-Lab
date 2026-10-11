# V99 Phase195-DT — UTC rollover integrity quarantine (2026-10-11)

Status: **DATA_ONLY/HOLD**. This is a research-only diagnostic; no champion promotion, holdout access, trading, frozen-engine change, or paper publication.

- Target research branch head inspected: `1d5733d0cea91514d38848ee08a776363ea23071`.
- Independently harvested GitHub Actions failed-publication archives from runs 38169443788, 38170249090, 38171174001, 38171975084, 38172804097.
- Combined **22 official candidate archives**; all **22/22** passed monetary accounting for eight tracks but **0/22** passed the immutable published-prefix guard (176 track-hour mutations in the 22 archive snapshots).
- **New integrity failure:** run **38170249090**, observed at `2026-10-11T20:00:21.885065Z`, declared `state/paper_v15_universe.json.verified_boundary=2026-10-11T18:00:00Z` while `reports/paper_data_sync_v15.json.target_latest_closed_hour=2026-10-11T19:00:00Z` and the paper ledgers also ended at 19:00Z. This archive is **quarantined** from the immutable runner-observation registry; its financial curve is not silently discarded or rewritten. The next run 38171174001 shows consistent 19:00Z boundaries. This is a race/atomicity risk at hour rollover, not proof of executed lookahead.
- Valid registry append-only continuity **17→21** confirmed, head SHA256 `af9f055b1165fc0fc73f84bbd3cda509abfcdff307f36913e606c3a59fa3dfc0`. 141 snapshot rows of runner-inferred temporal eligibility backdating and 198 repeated announcements, **not authenticated exchange-time receipts**.
- Latest valid candidate 38172804097: 243 paired hourly returns Oct 1 16:00Z–Oct 11 19:00Z, V99 **-4.9845%** vs V16 **-4.8850%** (not validated forward paper). Worst-10 hour overlap 9/10; relative log return -10.467 bps.
- Latest V15 universe: 175 persistent, 173 ready, 2 Unicode symbols failed bootstrap due to ASCII codec. No unexplained readiness gap.
- All six source-authenticated replay input classes still absent from these audit ZIPs; four-arm matched causal replay remains gated. Maintain closed-t to no-earlier-than t+1 execution, chronological train-only selection, untouched holdout, severe/supersevere costs, temporal folds, regime matrix, benchmark envelope.
- Local reproducible tool: `scripts/v99_phase195dt_rollover_quarantine.py` (not yet integrated into this branch); **57 local tests passed** including eight new boundary/quarantine tests. Artifacts and SHA256 manifests available in the cycle's evidence package.
- Existing frozen engines, durable paper-results, champion, and public dashboard are deliberately unchanged.

Preregistered next step: introduce a read-only **atomic-boundary witness** in the research branch; require agreement of verified source boundary, synced target, and all ledger timestamps before admitting a snapshot to any observation registry. Then obtain authenticated immutable source receipts and execute the four-arm matched replay without using this candidate-only PnL for promotion.
