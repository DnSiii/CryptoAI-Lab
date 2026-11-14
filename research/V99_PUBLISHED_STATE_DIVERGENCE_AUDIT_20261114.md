# V99 published-state divergence audit — 2026-11-14 23:47 UTC

Read-only comparison at immutable `paper-results` commit `92142fe105b1cb23f3f15f289f6c5a0331747dba`. **This is not an execution provenance certificate or an economic strategy validation.**

## Evidence from one commit
- `reports/paper_v13_snapshot.json` (blob `7ee84e7d3317111aaf14b73bd9b24b1ccd43d01c`): PAPER_ONLY, no real orders, 2235 forward hours, last closed hour 2026-11-14T22:00:00Z.
- `reports/paper_v99_snapshot.json` (blob `58cb5ea694ec1b094714ede61e0e580a56773ec9`): V99 Frozen checkpoint at 2026-11-14T22:00:00Z, no real orders.
- `reports/paper_v99_ledger.json` (blob `511382bebba9b8c44b70a97173ad97d08f6709b0`): 1656 simulated forward hours; capital R$ 9,672.90 from R$ 10,000; forward return -3.271003%. **Not realized PnL.**
- **Important divergence:** `reports/paper_v99_research_snapshot.json` (blob `2e01712f228fa8821ce3d6ea7da2399b1984dee4`) remains at **2026-10-10T05:00:00Z**, more than 35 days behind the V99 Frozen snapshot. Its simulated variant returns cannot be presented as current. Do not overwrite or backfill it to hide staleness.
- `reports/paper_data_sync_v13.json` (blob `3797c3157a95540b21b5f9b5f0ec5bdcf17b5d31`): generated 2026-11-14T23:38:37Z, target last closed hour 22:00Z, funding lag BTC/ETH 6 hours; FTM/MKR quarantined. Public Binance kline/funding is **not** original order/fill execution provenance.
- `reports/paper_runtime_status.json` (blob `f87e8c4399232370832af9b8da8e6061e1a4c593`): heartbeat 23:44:48Z, workflow 43654119822, operational only.
- Actions 43654119822 (paper) and 43654099923 (dashboard) concluded SUCCESS; Actions 43654788501 and 43654765189 were in progress when checked. Workflow success does not certify served GitHub Pages HTML.

## Required follow-up
1. Trace every dashboard selector for V99 Research to its actual source. If it uses the stale `paper_v99_research_snapshot.json`, display **STALE — last market hour 2026-10-10 05:00 UTC — research-only, no live orders**, without altering the historic paper.
2. Check public HTTP-served page and source commit; distinguish V99 Frozen forward paper from the separate research-five comparison.
3. Independently reconcile original raw notionals/position deltas and capture timestamps; no relaxation of strict subcent verifier and no synthetic trade recreation.
4. Only preregister and test a genuinely distinct complete engine on TRAIN with native costs and full original evidence; do not open validation or holdout.

No modifications to Frozen, paper-results, historical paper, legacy champion, validation, or holdout. No real orders and **NO PROMOTION**.
