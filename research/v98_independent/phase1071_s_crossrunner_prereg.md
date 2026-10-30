# V98 Independent Phase1071–1072 — S signed-source cross-runner preregistration (2026-10-23)

Architecture S Phase1068 remains the only current seven-slot candidate. This gate is **source-only**, cannot compute PnL, cannot promote/freeze S, and cannot read 2025 validation, 2026+, XRP, contaminated Phase083, or any V14/V15/V99 benchmark.

## Precommitted contracts
1. Independently reacquire 100 official Clean-4 OHLC ZIPs and 100 funding plus 100 mark archives, including the four February-2023 daily-source repairs, and verify original pinned checksums; no cached-pass shortcut.
2. Read 18,288 hourly rows (Dec-2022–Dec-2024), exactly 9,144 funding events, four assets only. Signed mark-low/high transport must be (18288,4,2), conservative vendor marks (18288,4); verify event times, sign, CSV SHA256 and complete native event mapping.
3. Produce five S target hashes after six-decimal conservative quantization and post-serialization gross/net/asset caps. Repeat target composition within each runner. Reject any mismatch.
4. Run independently provisioned Ubuntu 22.04 and 24.04 CI jobs with pinned Python 3.11, NumPy 1.26.4, pandas 2.2.3, SciPy 1.14.1. Require exact match of five hashes, vendor typed CSV hash, S code blob SHAs, source attestation and activation diagnostics.
5. On any failure, report BLOCKED_BEFORE_PNL, preserve both receipts and do not freeze or calculate economics. Do not repair S using observed historical PnL. Only after a full source PASS, freeze S source and preregister signed 90-cell economic execution (5 paths × 3 costs × 2 funding orders × 3 capital modes), then separate 2025 validation.

This document is not evidence of an official PASS or economic superiority. R and Q rejections remain immutable.