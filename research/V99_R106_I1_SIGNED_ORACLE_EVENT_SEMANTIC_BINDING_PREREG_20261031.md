# V99 I1 — signed original-event oracle semantic binding (2026-10-31 18:xx BRT)

**Source integrity only; no new strategy, historical economics, tuning, validation, holdout, Frozen/paper changes, or orders.**

## Identified remaining software bypass
The 2026-10-31 Ed25519 gate checks the auditor signature and seven exact file hashes, but does not parse the `independent_event_oracle_replay` evidence class. An independently signed package containing seven arbitrary, unrelated byte strings can therefore unlock a nonfixture wallet event even when no event-specific oracle replay exists. A signature attests to the signer's bytes, not to economic provenance or correct fee/venue accounting. The existing synthetic fixture demonstrates this gap.

## Ex-ante invariant and rejection tests
Before a nonfixture OPEN/MARK/SETTLE_BATCH is accepted, require the independently signed `independent_event_oracle_replay` file to be a strict UTF-8 JSON event binding:
- `schema = V99_I1_ORIGINAL_EVENT_INDEPENDENT_ORACLE_V1`, `fixture = false`, `event_sha256` exactly equals the canonical current event SHA256.
- `replay_status = PASS`, `historical_economic_train_certified = false`, `promotion_authorized = false`.
- A strict `bound_source_sha256` map must bind each of the **other six** signed evidence classes to their exact attested byte hashes. The independent oracle file itself is signed by the outer package. Reject duplicate JSON keys, extra/missing keys, malformed digests, mismatched hashes, wrong event or scenario, malformed JSON, and arbitrarily signed non-JSON oracle bytes.
- Maintain immutable signature-byte snapshot, fail-closed trust anchor, and all existing signed-evidence path checks. Reject intermediate symlink components, not just a symlink leaf. No self-asserted caller boolean or signed fixture can authorize promotion.
- Synthetic tests may create an illustrative oracle JSON signed by a **test-only** key; passing such tests is **never** original source or independent exchange evidence. The real nonfixture source remains blocked until independently controlled key/signature, lawful 661-day original Deribit options BBO/size/time lifecycle, original fees/contract/margin/delivery, and complete independent replay are delivered.
- Add adversarial controls for wrong event hash, unrelated source digest, duplicate JSON keys, fake `fixture=true`, arbitrary signed oracle bytes, and intermediate symlink. Keep existing signed-event fixture behavior and modeled severe/supersevere fee floors.
- Change only verifier, focused tests, and their existing CI workflow as necessary. Preregistration must precede implementation. Run real GitHub Actions CI and inspect results, but do **not** call CI success a trading result.

**Decision rule:** any absent or inconsistent oracle semantics => SOURCE HOLD, never a partial pass. An authentic event-specific oracle remains a necessary but insufficient prerequisite; full original economic TRAIN and gates stay locked.