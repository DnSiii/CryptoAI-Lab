# V99 R106 Phase195-FH — 2026-10-13 10:46 BRT

**Decision: DATA_ONLY/HOLD; no promotion, no holdout, no paper publication.**

## Official new observations (GitHub Actions)
Four new official paper audit ZIPs, all independently verified against Actions SHA-256 metadata:
- 38401312951 / 11815781820 / `4ad5d38ce61bfa56408d82e42b0f617cc99da01105e2e5cc44a583c2559842e6`
- 38402868145 / 11816144299 / `14060a137d679af42b76611d6a6f754f7465ea6d72b00a51a98dd202e4a8025b`
- 38404620224 / 11818991936 / `374eb75a654328d55279670eb4cc42aeaab8d9489202ee2cdc1fde083ba45d04`
- 38406458410 / 11819308270 / `bdeecf18833a1dd9c8c6d1ca35f4f56dbdf154bb756ad410a542eb0f918caaca`

Across 26 verified archives, only **7 distinct eight-track economic snapshots**; all four new ZIPs carry the same new 12:00 UTC economic hour (three redundant repeats). The existing 08:00 UTC candidate-prefix rewrite remains; all eight candidate ledgers differ from the accepted published baseline.

## Independent verification
- **208** snapshot/state/ledger parity checks passed across all eight tracks.
- **208** complete track-accounting checks, **252,186** track-hour records, passed.
- Dynamic universe audit: **243 repeated** new-symbol claims, **256 early-eligibility** claims, **12** symbols with changing reported first-seen timestamps. No independent first-party exchange as-of receipt or acquisition attestation. Absence of observed premature adjustment in the reported decisions does not prove data causality.
- Fixed forward candidate-only boundary 2026-10-01 16:00 UTC through 2026-10-13 12:00 UTC, **284 paired returns**: V99 **-7.854551%** / DD **10.913010%**; V16 **-8.028255%** / DD **11.114409%**. Relative compounded descriptive edge **+0.188866 percentage points**.
- Only **2/4** disjoint chronological folds positive; excluding 2026-10-13 reverses the edge. Fixed 24h-block resampling (4,000 draws, seed 195) positive in **38%** of draws; this is **not a confidence interval** and cannot support promotion.
- 175 inherited regression tests passed, 3 skipped, 1 intentionally deselected due to invalidated append-only premise. A separate synthetic append-only provenance registry prototype passed **14 adversarial tests**; no source authenticity attested and no live pipeline deployed.

## Mechanism and next preregistered work
Main workflow restores `state/paper_v15_universe.json` from the stale `paper-results` branch. Published-prefix integrity guard rejects historical equity-curve revisions, so the updated universe is never durably persisted; repeated new-symbol claims and drifting first-seen times follow. GitHub run 38406458410 again failed this guard after uploading the audit ZIP. Never disable the guard to publish contaminated history.

Research-only prototype: append-only hash-chained event registry with idempotent retries, immutable first-seen, no backdating, conservative closed-bar t-1 eligibility, and fail-closed malformed/conflicting receipts. It is **not** an exchange-authenticated PIT source; hash chains protect integrity, not origin. Before any A/B/C/D causal train-only replay, require independently verifiable first-party source payloads and acquisition timestamps, then severe/supersevere costs, 3x2 regimes, benchmark envelope, PF/DD/tails/concentration, reproducibility. Keep holdout sealed. No new champion, no dashboard/paper-results modification, V16/V99 Frozen unchanged.
