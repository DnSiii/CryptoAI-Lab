# V99 I1 — bind complete 661-day journal to independent signature (2026-10-31)

**Preimplementation defect:** existing signed replay authenticates individual OPEN/MARK/SETTLE_BATCH event bytes but accepts caller-supplied daily BTC/ETH source indices, fold-edge indices, regime labels, initial native collateral and 180-decision ledgers without an independent signature. Thus a signed event stream could be replayed with altered USD NAV/benchmark or fold attribution while every event attestation still verifies. Cross-scenario equality does not establish independent origin.

**Frozen scope and acceptance criteria (before implementation):**
1. Require a separate externally anchored Ed25519 signed **JOURNAL** attestation for any `replay_signed` / `--signed` nonfixture run, before processing events or creating an output. Reuse the existing signed-evidence gate and external auditor public-key SHA256 pin, with a canonical SHA256 digest of the **entire** journal excluding only its `journal_attestation` path. This binds every index, fold-edge index, regime, decision, event payload, fee, initial wallet, and scenario path. Do not trust a signature/key supplied in the journal itself.
2. Preserve the per-event signatures and all existing event validation; the journal signature is **additional**, not a substitute. Missing, altered, invalid or mismatched journal evidence must fail closed; signed fixtures remain forbidden. Fixture-only unsigned replay stays unchanged.
3. Extend the allowed signed digest type only to `JOURNAL`, retaining identical event digest semantics for OPEN/MARK/SETTLE_BATCH. No change to strategy, data, risk, cost, 661-day calendar, five folds, 3x2 regimes or any gates.
4. Add adversarial tests: absent journal attestation; changed daily index or regime after signing; mismatched journal digest; valid mocked routing that still reports PROVISIONAL and no promotion; existing signed-event and CLI tests must pass. A real ephemeral test key is **synthetic fixture only**.
5. Run actual GitHub Actions on the target branch and inspect results. Do not claim exchange-certified receipts, historical execution or ROI from a green test.
6. Never modify V16/V99 Frozen, champion, paper, sealed validation or holdout; no orders. 658/661 licensed Deribit original days, account-native fees, margin/liquidation/settlement receipts and an independent auditor's real trust anchor remain external requirements.

**Decision:** this closes a genuine signed-input tampering route; it does NOT unblock economic TRAIN without originals. No promotion.
