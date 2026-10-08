# Phase195-J: independent receipt payload parity (2026-10-08)

Status: DATA_ONLY, no economic trials.

Precommitted hypothesis: At Ethereum TRAIN block 17000000, all transaction receipts from dRPC bulk and Publicnode per-transaction RPC should agree exactly in transaction order, block identity, cumulative gas, status, receipt type, bloom and full ordered log payload. Require all 102 transaction hashes from a fixed canonical header. No partial success and no dropping mismatches.

Failure conditions: unavailable RPC, any missing receipt, any changed log, mismatched transaction index, bloom, block hash or status. Compare SHA256 of a canonical JSON payload; a matching digest is structural parity only, not receiptsRoot, historical latency, consensus or full TRAIN coverage.

Always HOLD for promotion, no PnL, no holdout, no changes to Frozen versions.