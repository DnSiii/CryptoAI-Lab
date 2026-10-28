# V99 I1 — original-signal handoff provenance re-execution preregistration (2026-10-27 22:xx BRT)

Status: SOURCE_ONLY/HOLD, NO PROMOTION. This is a correctness repair for the existing fixed 90-week I1 signal-to-source handoff, not a new strategy, retune, ROI, or economic validation.

## Discovered integrity gap
The handoff accepts a user-provided 182-row JSON with `source_original: true`, matching calendar and folds, but does not independently recompute its original BTC/ETH OKX spot and Deribit DVOL signal values at handoff time. The input's SHA256 is only self-hashed and does not authenticate the upstream market receipts. A forged positive signal with the correct 182-row schedule could pass the handoff's source-only intersection and inflate apparent source eligibility.

## Fixed repair and adversarial acceptance
1. In the existing fixed-handoff GitHub Actions workflow, restore the already archived ORIGINAL TRAIN-only OKX spot receipts from run 40019588739 and Deribit DVOL receipts from run 40072202459, alongside the frozen original signal artifact from run 40326586848. Never fetch any validation/holdout or post-2023-09-30 market data.
2. Run the independent pre-existing `research.verification.independent_v99_r106_i1_causal_signal_oracle` against those original receipts and the downloaded original signal JSON. It must verify all 182 decisions, all five chronological TRAIN folds, t-1 RV/DVOL, and the tamper/future-leak controls before the fixed 180-week source join is allowed. A modified signal field or source receipt must stop CI; do not silently accept self-declared `source_original`.
3. Add an adversarial unit test showing a fabricated positive signal with a correct schedule and fold can otherwise pass a purely structural `join_reports` call. Make the actual workflow explicitly fail closed by requiring the independent upstream oracle, not by presenting this structural unit check as certification.
4. Keep the existing 661-day fixture/independent-byte integration check, and the real missing licensed Deribit options archive gate. A green CI is software/source-integrity evidence only. 0 certified complete option lifecycles, no economic TRAIN/ROI/fills, no orders, no paper/Frozen/champion/holdout modifications.

## Expected outcome
CI should either show the upstream original signal independently reproduced and then BLOCKED_ORIGINAL_LIFECYCLE_ARCHIVE_MISSING, or fail at the exact missing/tampered original source. The downstream economic TRAIN remains blocked by licensed 2021–2023 original BTC/ETH options quotes and dated native terms. No candidate promotion.
