# V99 R106 Phase191 — Blockscout probe implementation

Date: 2026-09-30
Scope: DATA_ONLY; economic trial counter remains 0.

Implemented `research/tools/v99_phase191_blockscout_receipt_probe.py` after the preregistration at `docs/research/v99_phase191_blockscout_receipt_preregister_20260930.md`.

The probe is deliberately fail-closed. It validates Ethereum mainnet canonical USDC/USDT emitter identity, 32-byte block and transaction hashes, nonempty integer/hex log index, topics/data structure, and duplicate canonical identities. It never infers or repairs missing log index and reads no prices, PnL, regime labels, benchmarks, validation outcomes, or holdout.

This first implementation is only a source-schema/identity probe. It does NOT claim that the full three frozen TRAIN windows passed, and it does NOT authorize economic testing. Full Phase191 approval still requires all preregistered gates: same three TRAIN windows, issuer-specific semantics, conflict checks, independent finality, deterministic double-run, causal t-1 aggregation, and complete pass for both assets.

A connector safety gate prevented adding the companion pytest file in this invocation; this is a tooling event, not a scientific result. The production probe itself was committed as `f309d7b8`. No V16 Frozen or V99 Frozen file was modified.

Next: execute/CI the schema probe; if and only if it succeeds, extend the same fail-closed implementation to receipt-verifiable frozen-window coverage and independent finality. Economic trial counter remains zero until the entire DATA_ONLY gate passes.