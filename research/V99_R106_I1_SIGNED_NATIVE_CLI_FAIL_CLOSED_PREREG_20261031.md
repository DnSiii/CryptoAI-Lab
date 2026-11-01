# V99 I1 — signed native 661-day CLI: fail-closed execution preregistration (2026-10-31)

**Problem found before implementation:** `replay_signed(document)` exists, but the `python -m research.tools.v99_r106_i1_native_event_equity` command always calls unsigned `replay(document)`. A historical nonfixture JSON can therefore be processed by the command without independent event attestations, even though its output is marked provisional. This is a real runner-interface gap, not an economic strategy failure.

**Fixed acceptance criteria, no strategy retune:**
1. Keep `replay`/`replay_signed` APIs, 661-day grid, 180 fixed decisions, original market-path, cost, 5-fold, 3x2 regime, no-promotion flags, immutable research boundaries unchanged.
2. Command with two paths remains available **only for `fixture=True`** synthetic diagnostics. For `fixture=False`, require an explicit `--signed` command argument. Never silently downgrade signed mode to unsigned mode.
3. `--signed` invokes `replay_signed` (every OPEN/MARK/SETTLE_BATCH passes the existing independent Ed25519 event/source gate). Reject fixtures, missing trust anchor, missing/invalid signatures, and any nonfixture empty event journal. On failure, create **no output**.
4. Tests must exercise unsigned nonfixture CLI rejection, signed fixture rejection, missing external auditor trust-anchor rejection, and successful signed-mode dispatch under clearly mocked fixture-only attestations, without any historical economic certification or promotion. Run actual GitHub CI on the branch and record result.
5. No changes to frozen V16/V99, paper, champion, validation or holdout. No orders. Missing licensed 658/661 original option days and dated native fee/margin/liquidation/settlement records remain external blockers. A passing synthetic CI is not economic TRAIN.
