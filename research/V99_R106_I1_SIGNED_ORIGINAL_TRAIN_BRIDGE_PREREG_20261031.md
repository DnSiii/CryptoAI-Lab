# V99 I1 signed-original source-to-numeric bridge — preregistration (2026-10-31)

**Scope:** TRAIN 2021-12-09 through 2023-09-30 ONLY; no validation or holdout. Never use C1, frozen models, paper or order APIs.

## Concrete defect / integration gap

The existing source-driven 661-day original BBO+signal+event-spine+independent numeric audit in `v99_r106_i1_original_to_provisional_numeric.run` and the Ed25519 independently signed whole-journal/per-event native-wallet replay in `v99_r106_i1_native_event_equity.replay_signed` are separate commands. A signed result alone does not establish original BBO/complete lifecycle, and a source-bound provisional result alone does not establish auditor-signed event provenance. No single fail-closed, source-first, signed-second run currently cross-checks their entire economic output.

## Fixed implementation / veto rules

1. Inputs are exactly original causal signal JSON, complete original 661-day option quote root, nonfixture two-scenario journal JSON, output JSON. Reject fixture, missing or self-declared certification, missing source archive and missing external auditor key; no output on failure.
2. First run the existing original-intent, full original quote/entry book, source-cash veto, held-contract source spine, independent market path, native provisional equity and independent numeric oracles **before** any signed economic replay. Do not weaken existing requirements.
3. Only after original source checks pass, run the existing `replay_signed` with the externally pinned auditor key and exact journal/per-event attestations. Re-run `evaluate_provisional` and its independent oracle. Require byte-for-byte canonical equality of complete numeric report with the source-bound provisional report, including both scenarios, 661 days, 5 chronological folds, six regimes, severe/supersevere cost paths, tails, benchmark, drawdown. Require same 661d equity and fold snapshot source inputs across signed and unsigned replays by independently reproducing the existing unsigned event ledger; no partial run output.
4. On success emit only a **provisional, uncertified** joined diagnostic; never set `economic_train_certified`, `freeze_authorized`, `promotion_authorized`, `orders_enabled`, `validation_opened`, `holdout_opened` or paper publication. This bridge cannot replace historical native account fee/margin/lot/delivery/fill evidence or independent external audit.
5. Adversarial tests: fixture veto; missing 661-day source veto; absent trusted auditor key veto after source passes; mismatched signed-vs-source numeric veto; signed+source full success is **synthetic technical test only**, never market evidence. CI should execute technical controls and original-byte signal/partial-source join, and report current source hold accurately.

## Precommitted decision

Any missing licensed 661-day original BBO/size/arrival tape, dated native account fee/lot/margin/liquidation/delivery terms, original execution/fill evidence or external independent Ed25519 auditor trust anchor keeps **SOURCE HOLD / NO PROMOTION**. No ROI or trades inferred from fixtures, success status, or hypothetical fills.
