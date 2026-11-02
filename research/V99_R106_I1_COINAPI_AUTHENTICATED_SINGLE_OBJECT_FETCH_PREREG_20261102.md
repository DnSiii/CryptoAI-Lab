# V99 I1 — authenticated original CoinAPI single-object acquisition prereg (2026-11-02)

**TRAIN-only source transport; no economic certification, no orders, no validation/holdout access.** This is a transport closure for the existing fixed I1 architecture, NOT a new candidate, strategy grid, or PnL result. C1 and other rejected architectures remain rejected.

## Ex-ante source contract

Accept exactly one operator-selected CoinAPI Flat Files S3 **T-QUOTES / DERIBIT / BTC-or-ETH put** object, whose key and instrument must match the existing original partition validator and lie before 2023-10-01. Require a nonempty locally supplied written license document with a matching SHA-256, and a CoinAPI key from the process environment (never print or upload it). HEAD/GET may be billable: make both strictly opt-in by an explicit CLI authorization flag; never fetch or purchase automatically from an hourly automation. No key or authorization means **zero provider calls** and a blocked status.

Preflight HEAD ContentLength must be positive and <= 2 GiB before GET. Download only the exact named original compressed object into a same-directory private temporary file. Verify actual compressed length, original gzip/CSV through EOF, both provider timestamps, source symbol/partition, executable-vs-nonexecutable quote distinctions, and SHA-256 by the existing CoinAPI original-byte intake. Fail closed on truncation, corruption, changed bytes, invalid identity, provider denial, symlink/unsafe destination or overwrite. Publish original bytes and a non-promoting JSON sidecar **only after all checks**, via exclusive same-directory hardlinks. ETag is not SHA-256 proof. Never put licensed bytes, keys, or license document in public CI artifacts.

## Execution and falsification

Implement one standalone source downloader, adversarial tests (missing key, no billable consent, oversized HEAD, incomplete GET, corrupted gzip, sealed key, changed license, immutable successful publication), and a GitHub CI workflow running tests plus a **real no-key fail-closed CLI attempt**. With no entitlement, report the exact external blocker, not a fictitious economic TRAIN. This object transport does not establish 661-day coverage, native lots, historical fees, margin/liquidation, delivery index, hypothetical fills, independent economic replay, or a superior V99. Remain **SOURCE HOLD — NO PROMOTION** until original evidence and all preregistered economic gates exist.
