# V99 I1 signed original-source bridge: fail-closed atomic result publication (preregistered 2026-11-01)

## Concrete existing defect and scope
`research.tools.v99_r106_i1_signed_original_train_bridge.main` writes the source-joined, signed 661d result directly with `target.open("x")`. This prevents replacing an existing path, but leaves a partially written report if serialization, I/O or process termination fails. A concurrent observer can mistake that partial report for a complete signed result. The upstream original-to-provisional CLI also writes with `write_text`, but is outside this change; do not conflate provisional output with certified economics.

## Fixed change BEFORE implementation
Keep all source-first and independently signed accounting checks, immutable TRAIN fold edges, dual scenarios, strict 180 decisions, and all no-promotion flags unchanged. For the signed original-source bridge CLI only: reject any existing output (including symlinks) before expensive source replay; serialize to a same-directory temporary file, flush and fsync, then publish by exclusive hard-link creation so concurrent writers cannot overwrite one another. Cleanup temporary files in all success/failure paths. Do not write or replace any original signal, archive, journal, Frozen, paper, champion or sealed validation/holdout file.

## Adversarial tests
1. Existing output, including symlink, is rejected before running any source replay.
2. Serialization failure leaves no visible output or temp files.
3. Another writer creating the target during replay remains untouched, with no overwrite.
4. Successful source-mocked signed bridge preserves exact unpromoted JSON payload and no-promotion flags.
5. Execute GitHub CI and real original-byte source gate; report 0/182 original intersections as a blocker, not a numeric trading result.

## Scientific status
This is a data-integrity prerequisite, **not** alpha, economic TRAIN, independent original execution certification, or a reason to unlock validation/holdout. The full historical BTC/ETH Deribit executable option archive remains externally incomplete (658/661 days absent) and native account fee/lot/margin/liquidation/delivery/fill receipts and independent auditor trust anchor remain required. No orders, no synthetic promotion, no claimed ROI.
