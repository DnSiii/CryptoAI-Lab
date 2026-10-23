# V99 R106 D1 C165 — independent 216-hour two-scenario warmup/account bridge (2026-10-23 BRT)

**Decision: DATA_ONLY/HOLD — NO PROMOTION.** No authenticated historical ROI, economic TRAIN, validation, holdout, paper publication, orders or changes to Frozen/champion.

## Exact source-only change
- Branch `research/v99-r106-native-all-regime-engine`, baseline `9715c07ce1b88f990c035354db018d2b08f9c868`.
- Added independent `research/verification/independent_d1_c165_two_cost_path_bridge.py`, adversarial `research/tests/test_v99_r106_d1_c165_two_cost_path_bridge.py`, and `.github/workflows/v99-r106-d1-c165-two-cost-path-bridge.yml`. All three were additive; no existing file was modified/deleted.
- No C1/C2 retuning, no new alpha feature search. This is integration hardening of the *single* distinct preregistered D1 basis-carry candidate.

## Actually executed
- GitHub Actions run **39998551528**, job **120568348928**, commit `b6bb4bd8d8efce9e1ba97ecbc63b02f5db08cd68`: **completed / success**. Original logs inspected.
- **58/58 pytest** (10 new C165 tests + 48 C128/C129/C140 ledger tests); **87/87 earlier independent unittest regressions**; **145/145 total**. Explicit permissions assertion passed.
- A **216-hour synthetic**, same-start-capital, BTC/ETH spot+perp scenario pair was actually built and replayed. Each scenario included **168 flat warmup hours**, **2 daily decisions** after warmup and **54 modeled funding events** (27 per asset). Severe and supersevere paths were independently re-executed through C149/C150.
- Negative controls rejected mismatched exogenous prices/funding, invented warmup fills, tampered accounting state, incomplete cost paths, missing decision grid, sealed future time and forged permission. The modeled journal constructor, independent oracle and test fixture are separate source modules.

## What this proves and does not prove
- It proves **synthetic integration** of the existing C140 decision/fill/cash ledger with the independent C149/C150 oracle, under two cost scenarios and a proper 168h cold start. It does **not** prove any profit, authentic OKX historical fees, settled funding, executable native lots, fills, or live feasibility.
- Labels `OKX` in synthetic funding/market rows are caller-controlled strings; not exchange signatures or first-party historical receipts. C151 synthetic native lot diagnostics remain non-certifying.
- This 216h fixture is NOT the preregistered 15,864h TRAIN; it is NOT a five-fold result, NOT a six-regime result and NOT an independent historical validation. Neither the 2023-10-01 validation boundary nor the >=2024-01-18 final holdout was opened.

## Next justified work (no serial PnL fishing)
1. Source-only integrate exact original C141–C147/C152 modules if their verifiable source artifacts can be recovered, without replacing existing C127–C140/C153–C165 source; rerun full regression plus 15,864h *structural* gates.
2. Bind the already separate first-party OKX collection to timestamped **actual** paired BTC/ETH spot/perp marks, dated native instrument lot terms, account-specific fee tiers, historical funding settlements and execution/fill/slippage receipts. Fail closed on gaps, as-of ambiguities or synthetic substitutions; no made-up values.
3. Only after source/provenance closure, execute the **one** preregistered D1 TRAIN economic trial with 5 chronological folds, both severe cost paths, 3x2 regimes, tail concentration, DD, passive benchmarks and independent accounting. Reject on gates; freeze a genuinely qualified TRAIN candidate before opening sealed validation. Final holdout stays locked until formal authorization.

**No historical economic trial dispatched; no order submission; no promotion.**
