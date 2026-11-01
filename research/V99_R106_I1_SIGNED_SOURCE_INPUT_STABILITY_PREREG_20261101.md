# V99 I1 signed-original bridge input stability — preregistration (2026-11-01)

Scope: TRAIN-only original causal signal and 661-day original option manifest. No validation/holdout, no orders, no model promotion.

Defect: the signed-original bridge snapshots the native journal but does not bind the original causal signal and 661-day archive manifest to immutable bytes across its source-first verification and later signed replay. A caller may change either input after independent source verification without the joined diagnostic recording or detecting that mutation.

Fixed rule before implementation: read the signal and archive manifest bytes at entry when present; do not bypass the existing source-first missing-archive veto. Once source verification succeeds, require both inputs, SHA-256 equality with entry snapshots, and manifest SHA-256 equality with the source verifier's reported original_quote_manifest_sha256. Recheck both inputs after the signed/native and independent numeric replay. Any mismatch must fail closed before publishing the output. Report both digests as INPUT IDENTIFIERS ONLY, not historical execution certification.

Adversarial controls: source mutates signal; source mutates manifest; source claims wrong manifest digest; mutation during signed replay; unmodified mocked technical bridge still unpromoted. CI must run these alongside the original independent partial-source blocker. Tests with mocked source or temporary signatures are not market evidence.

External hold remains: licensed original complete 661-day option BBO/size/arrival tape, account-native fee/lot/margin/liquidation/delivery and actual fill evidence, independently controlled Ed25519 trust anchor. No economic TRAIN/ROI, freeze, promotion, paper or order permission from this change.
