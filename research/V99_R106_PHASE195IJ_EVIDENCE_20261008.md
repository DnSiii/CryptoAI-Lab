# V99 Phase195-I/J evidence — 2026-10-08

Research branch only. All results DATA_ONLY, no economic trials.

Phase195-I GitHub Actions run 37827740580: 16 synthetic controls passed. At fixed TRAIN block 17000000, dRPC blockHash queries for Mint and Burn returned zero logs, and Burn height-range returned zero. Mint height-range returned HTTP 400. Publicnode height-range returned HTTP 403 and blockHash returned RPC 4444. No four-way log parity; no source integrity approval.

Phase195-J GitHub Actions run 37828026089: 5 synthetic tests passed. dRPC 102 bulk receipts and 102 individual receipts matched the same canonical payload digest, with 237 logs. Publicnode individual receipt query returned null for at least one fixed index, so independent payload parity failed. No receiptsRoot cryptographic reconstruction or consensus anchoring.

Paper audit: paper-results and gh-pages dashboard_data.json share blob 4fe7a60c6a41e4d3aa08cc0cc5a8a998585f24a9, 5301733 bytes. All five tracks have 532 hourly points and zero time gaps from 2026-09-16 13:00Z to 2026-10-08 16:00Z. F1/F3 remain research_rejected regardless of paper ROI; F7 remains research_leader. No champion promotion.

Next: record fixed publicnode receipt probe indices and reconstruct canonical receiptsRoot from the complete dRPC bulk receipts, still DATA_ONLY until independent consensus, latency and full TRAIN coverage. Frozen versions and holdout untouched.
