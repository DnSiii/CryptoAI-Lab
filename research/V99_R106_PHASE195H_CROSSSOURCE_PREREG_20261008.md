# Phase195-G result and Phase195-H preregistration (2026-10-08)

DATA_ONLY, zero economic trials, holdout untouched. Actions 37819709674: 11 synthetic tests passed. At fixed TRAIN block 17000000, publicnode returned both headers but HTTP 403 for mint and burn log queries; drpc returned headers, 102 unverified receipts and zero mint/burn logs; llamarpc returned HTTP 525 on chainId.

Phase195-H preregistered before execution: compare publicnode and drpc fixed-block header fields; validate drpc receipts against transaction count, index ordering, block linkage, gas monotonicity and complete global log ordering; compare native Mint/Burn logs to drpc eth_getLogs. Any mismatch is HOLD. Never access holdout or prices. Even a match remains structural-only: no receiptsRoot reconstruction, consensus anchor, provider independence, t-1 latency or complete TRAIN coverage is established. No PnL, promotion or dashboard champion change. V16/V99 Frozen and all original economic gates remain untouched.
