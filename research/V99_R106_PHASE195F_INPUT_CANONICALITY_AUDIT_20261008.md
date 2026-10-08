# V99 R106 — Phase195-F source-input hardening (2026-10-08)

**DATA_ONLY; economic_trials=0; HOLD_UNPROVEN_SOURCE.** This is a source-integrity audit, not an economic hypothesis or candidate promotion. Frozen V16/V99, holdout, t-1, chronological folds, severe/supersevere costs, regime matrix and benchmark envelope remain unchanged.

## Independently observed failure mechanisms
- Python int(hex,16) accepts signs, underscores and whitespace. Strict JSON-RPC QUANTITY grammar is required.
- Default json.loads accepts duplicate keys and NaN/Infinity. Reject ambiguous or nonfinite provider evidence.
- Nondecreasing timestamps accept identical parent-child timestamps; require strict increase.
- Header-only TRAIN boundary sentinels must reject native-event digests and all receipt-verification claims.

## Local Phase195-D/E corrective evidence
The local research bundle was hardened and nine synthetic test programs passed. 5 canonical quantity cases accepted, 17 malformed quantity cases rejected, 5 structural adversarial cases rejected. Deterministic 100,000-block-per-operator streaming replay passed twice, folds [129,129,130,129,129,130], digest 7cf4630a838fca438a4144abea2d34e6a8fa30aa7eb55437de4f7003ce144d4c. **Synthetic tests do not certify real chain data.**

The separately committed Phase195-F single-stream firewall is an independent, fail-closed parser layer. It returns SINGLE_STREAM_CLAIMS_SYNTAX_ONLY, never real-chain PASS, never permission for PnL.

## Independent Phase192 artifact harvest
GitHub Actions run 37365676577 completed 2026-10-05 as DATA_ONLY. Snapshot SHA256 de5a6303170e71e0576a4fe7ec66b7094f131bee3ca7b8aaf3dcc95c65799aaa; 914 cached requests; 903385 cached rows; 893000 duplicate appearances; 10385 unique log identities; 12 token/event/window cells. Three disconnected windows fail 776 continuous interior TRAIN days. H194A remains rejected before economics.

## Next gate
Publish and validate complete Phase195-B/D receiptsRoot and Phase195-E paired full-TRAIN gates. Require independent consensus header, independently owned archival operators, all ordered receipts/unrelated logs, historical t-1 publication latency, and 778/776 calendar coverage. No new validated champion, so preserve dashboard champion and paper history.
