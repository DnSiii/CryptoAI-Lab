# V99 R106 D1 C163 — original C139 execution adapter and independent native-lot integration (2026-10-23 BRT)

**Decision: DATA_ONLY/HOLD — NO PROMOTION.** No historical economic TRAIN, validated market ROI, real orders, paper-results, sealed validation or final holdout.

## Verified deployment and CI
- Target: `research/v99-r106-native-all-regime-engine`. Base commit `651cf40b210b1dd433f7e19619a5f23a83f89cd4`, CI source commit `023d39448e5502cebef162b5b1277fb8e1c76294`.
- Deployed the **original unmodified C139 preregistered target -> paired BTC/ETH spot/perp modeled-fill adapter**, blob `cf07b363f10069590a4f9ecc524e0ded2a2bb327`, independently compared to the existing C152/C153 local package; exact match.
- Deployed the **original unmodified C139 10-test suite**, blob `b981cbdbf25fb4c4853d82ab550ba41601d1b7e2`; exact local-package match. Added three independent cross-module C139 -> existing C151 executable-lot tests and one read-only CI workflow.
- GitHub compare of base -> CI commit: **four files added; zero existing files modified/deleted**. No Frozen V16/V99, paper/results, champion, existing strategy thresholds or prior research results touched.
- GitHub Actions **39981456076**, job **120509519040**: completed SUCCESS on source commit `023d394`; original C139 + new integration **13/13** tests and prior C162-C153 chain **74/74** tests, **87/87 total**. Remote logs inspected, permission fail-closed step green. Original C139 suite also passed locally **10/10** before deployment.

## Independent modeled-fill / lot evidence (NOT exchange evidence)
- From the fixed synthetic `2023-09-29T00:00:00Z` cold-cash fixture, each cost scenario produced **4 modeled paired-leg fills** (BTC/ETH spot + perpetual); **4/4 fail** the **illustrative unauthenticated** C151 lot/contract grid. The C151 hard veto correctly rejects both scenarios. This does **not** establish real OKX lot violations, because the historical instrument terms are not authenticated.
- Severe: synthetic native fee `0.7448122463788095965` quote and stress fee `0.6968290915022984351`; supersevere: identical synthetic native fee and stress fee `1.3936581830045968702`. Resulting synthetic NAVs `998.5583586621188919684` vs `997.8615295706165935333` from identical starting quote `1000`. **These are deterministic artificial fee-accounting examples, NOT ROI or trading profits.**
- Separate checks confirm exact net-base hedge, no borrowing, <=1x post-fee gross, t-1 feature timestamp, scenario fee identities, sealed TRAIN-only bounds, and that future-published instrument terms fail closed.

## Blocking gates and next justified action
1. Additively integrate the original C128 cash-inventory, C135 mark-fill and C129 hourly-account modules plus their independent tests; then C140 hourly journal. Never alter preregistered D1 economic parameters to fix modeled lot violations. Re-run remote source-only CI and independent accounting.
2. Require first-party historically as-of BTC/ETH spot+swap paired marks, native fee tiers, funding fixes and **actual settled funding**, dated instrument lot/contract specifications and execution/fill/slippage receipts before any economic TRAIN scoring. An OKX-looking string, SHA, synthetic test or successful Action is not authentication.
3. A genuine historical TRAIN must cover five chronological folds, 3x2 regimes, severe/supersevere, tail concentration, drawdown, four passive benchmarks, independent accounting, and executable lots; freeze a passing D1 before opening validation `[2023-10-01,2024-01-18)`. Final holdout `>=2024-01-18` stays sealed. Rejected C1/C2 and archived alpha remain rejected.

**No economic CI run, no promotion, no orders.**
