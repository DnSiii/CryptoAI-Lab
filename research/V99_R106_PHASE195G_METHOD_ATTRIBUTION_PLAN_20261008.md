# Phase195-G — fixed TRAIN archival method attribution (2026-10-08)

DATA_ONLY; economic_trials=0; holdout_accessed=false. Fixed preregistered Ethereum block 17,000,000. GitHub Actions runs 37812227829 and 37812693613 failed closed. In run 37812693613, chainId 0x1 was observed for publicnode and drpc, whereas llamarpc returned HTTP 525. The sequential archival preflight masks the HTTP status of the first failing historical RPC method.

Preregistered independent checks: chainId, finalized header, fixed TRAIN header, fixed-block USDC mint logs, fixed-block burn logs, and fixed-block receipts. Record method-level HTTP/RPC codes only, bounded untrusted response shapes, no raw provider bodies. All checks are DATA_ONLY; even HTTP 200 everywhere does not establish independent consensus, receiptsRoot, complete historical coverage, operator independence or t-1 availability.

No PnL, no candidate promotion, no holdout access, no frozen version changes. Keep chronological train-only selection, temporal folds, severe/supersevere costs, regime matrix, benchmark envelope and anti-overfit discipline. Dashboard champion and durable paper-results unchanged.
