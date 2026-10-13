# V99 R106 Phase195-FI — atomic-boundary witness and official dual-run audit

Date: 2026-10-13 UTC. Branch: `research/v99-r106-native-all-regime-engine`.

**Decision: DATA_ONLY/HOLD.** No economic strategy test or promotion by Phase195-FI, no paper-history publication, no V16/V99 Frozen edits, no holdout access.

## Preregistered motivation

The existing Phase195-DT quarantine identified a runner-hour rollover with `verified_boundary` one hour behind the sync target. The preexisting follow-up required a read-only atomic-boundary witness before admitting any reconstructed runner artifact. This implements that narrow, source-neutral invariant. It does not use candidate returns or tune any trading signal.

## Official inputs and byte hashes

Two **different official GitHub Actions runs**, each with an independent signed Actions artifact digest:

| Workflow run | Artifact ID | ZIP SHA-256 | Distinct economic hour |
| --- | --- | --- | --- |
| `38427711550` | `11829258013` | `b2bae307536f62c15990e31809a3ea2ffdd9b6a47ac0516d175c906452ef6407` | 2026-10-13 15:00 UTC |
| `38429212299` | `11830268860` | `c94dd113b60f127b04ad93efe8e7a244bf14e4a59beb1867230cdf278eb58da2` | 2026-10-13 15:00 UTC |

Both ZIPs were fetched independently from their actual GitHub Actions artifact IDs; local byte SHA-256 matches GitHub Actions digest in both cases. Their byte hashes differ because capture/metadata differ; the **eight candidate equity curves are identical across the two runs**. These two runs therefore do **not** provide independent economic evidence.

## Witness implementation and validation

Files committed in the research branch:
- `research/tools/v99_phase195fi_atomic_boundary_witness.py`
- `research/tests/test_phase195fi_atomic_boundary_witness.py`
- `.github/workflows/v99-r106-phase195fi-boundary.yml`

Code SHA-256 (locally validated, Git blob hashes independently matched GitHub):
- tool `1e025becfd26cbd9c96a4bc7c7e5af294bff90ebf5d5cf3111dfd85c2da19117`
- tests `115990876ee2335199eba570523495e29d0e7aab945759bc35db08c4aa13d375`

**24 adversarial tests passed locally** and the branch's Python 3.12 GitHub workflow run `38431703098` passed. Tests cover missing and duplicate timestamps/ZIP members/JSON keys, nonfinite values, boundary disagreement, forward/stale ledger, non-hourly gaps, wrong modes and flags, early captures, and legacy ledger/snapshot mismatch.

Seven historical ledger schemas omit `real_orders_enabled`; their companion snapshots explicitly provide `false`. The witness requires a companion false flag for any ledger lacking it and never treats the missing field as authorization.

Both actual official artifacts passed the **structural boundary witness**:
- `verified_boundary == target_latest_closed_hour == expected_latest_closed_hour == 2026-10-13 15:00 UTC`;
- all eight paper ledger latest timestamps, last curve rows and snapshots equal that hour;
- the eight per-track curves are whole-hour contiguous, each on its **own original paper boundary**;
- generated sync and universe capture timestamps follow the relevant hour close.

Status returned: `OBSERVED_BOUNDARY_CONSISTENT_NOT_AUTHENTICATED`. Even on success, `source_time_authenticated=false`, `append_only_prefix_certified=false`, `publication_authorized=false`, `promotion_authorized=false`, `holdout_accessed=false`, `economic_trials=0` (for this audit).

## Separate still-failing published-prefix gate

In **each** of these official ZIPs, each of the eight candidate ledgers:
- has **exactly one rewritten published equity hour**, `2026-10-01T16:00:00+00:00`;
- has **no omitted published hours** and **287 new post-publication hours**;
- changes the historical recorded capital of that published hour and therefore remains **inadmissible for durable paper publication**.

The seven tracks carrying funding decomposition show delayed negative funding at the rewritten hour: V13 -R$0.47, core -R$0.42, opportunity -R$0.05, combined -R$0.49, V14 -R$0.45, V15 -R$0.44, V16 -R$0.36. V99's same published hour changes capital R$9263.27→R$9262.91, but its ledger **does not** expose per-hour funding components, so the V99 delta **cannot be independently attributed to funding**. For multiple tracks, cent-level rounding also differs.

**A consistent snapshot can still contain rewritten published history.** The separate immutable-prefix integrity guard correctly blocks publication and must not be weakened.

## Decision and ordered next gates

1. Keep Phase195-FI as a **research-only read-only witness**. It must never grant publication or source-PIT certification.
2. Obtain authentic raw as-of exchange payloads plus independently attestable reception timestamps. Github ZIP hashing is byte-integrity evidence, not proof of when an exchange published a candle/funding settlement.
3. Preregister and validate a forward-recovery protocol that preserves **every published byte**. Compare two safe options in a separate sandbox only: (A) replay from immutable as-published inputs; (B) a later-hour, disclosed correction entry with independently authenticated source provenance and complete accounting. Never silently rewrite the 2026-10-01 hour or splice an inconsistent cumulative curve.
4. Then require protected chronological TRAIN-only replay, causal t−1/latency, severe/supersevere costs, temporal folds, 3×2 regimes, benchmark envelope, concentration/tails, reproducibility, and untouched final holdout **before** any economic promotion.

**No production paper publication, new champion, economic improvement, or full-source PIT gate has been proven here.**
