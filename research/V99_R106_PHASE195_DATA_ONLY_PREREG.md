# V99 R106 Phase195 — DATA_ONLY preregistration
Status: PRE-ECONOMIC SOURCE-INTEGRITY STUDY; economic_trials=0.
Parent evidence: Phase194A is permanently rejected before economic trial; this is an independent new data study, not a repair or retest.

## Frozen data envelope
Ethereum mainnet (chainId 1), issuer-native USDC 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48. Only Mint topic 0xab8530f87dc9b59234c4623bf917212bb2536d647574c8e7e5da92c2ede0c9f8 and Burn topic 0xcc16f5dbb4873280815c1ee09dbd06736cffcc184412cf7a71a0fdb75d397ca5. TRAIN block timestamps >= 2021-12-01T00:00:00Z and < 2024-01-18T00:00:00Z, pinned to Phase182 frozen TRAIN evaluator blob 8ebe3f87e7617760857a861eac690df6971efbdd. No out-of-TRAIN event query. Boundary discovery may read headers only. First/last boundary days NA; 776 interior UTC days target. Six fixed chronological coverage folds.

## Data-only protocol
Acquire consecutive finalized block headers (number, hash, parentHash, timestamp), Mint/Burn logs and all block transaction receipts in bounded 256-block chunks from two independently operated archival providers. Verify every header chain link, canonical event identity (blockHash, transactionHash, logIndex), block-global logIndex uniqueness, no moved transaction, no reorg conflict, no missing/truncated page, complete block receipts and independently identical provider results. Treat any unproven completeness as NA, never zero. A daily zero requires full canonical contiguous block chain, both topic coverage and boundary sentinels. Preserve immutable canonical-byte checkpoints and externally anchored SHA256 index; verify replay byte identity, adversarial mutations, overlap and future-mutation invariance.

## Causal/economic firewall
A source day is eligible only when source_end < decision_timestamp and source_end+3600s < decision_timestamp, subject to independent proof of historical publication latency. No market returns, costs, benchmarks, regimes, holdout or economic optimization may be accessed by Phase195. If any provenance, continuity, coverage or causal gate fails, reject/HOLD DATA_ONLY, economic_trials=0. If ALL pass, authorize only a distinct separately preregistered TRAIN-only economic hypothesis. Any subsequent hypothesis must preserve t-1, chronological selection, temporal folds, severe/supersevere costs, full regime matrix, benchmark envelope, tail concentration, deterministic reproducibility and untouched holdout. V16 Frozen and V99 Frozen immutable.

## Evidence classification
Synthetic/mock unit and stress tests prove implementation invariants ONLY; they do not establish historical source coverage, independent provenance, or alpha. Do not begin real acquisition until this preregistration is committed.