# V99 R106 D1 — C157/C158 independent accounting and five-fold risk integration (2026-10-23 BRT)

**Decision: DATA_ONLY/HOLD — NO PROMOTION.** No exchange-authenticated historical economic TRAIN, validation, final holdout, real orders, paper/results or profit claims.

## Remote execution and immutable scope
- Base branch head before cycle: `b744a4c41b7b61bbe879592d6c7ffc307f88a50d`.
- C157 published C149 independent Decimal accounting oracle, C150 cold-start/warmup oracle, adversarial 169-hour two-scenario synthetic tests, and a source-only workflow.
- Initial C157 Action **39941736406** failed **1/44** tests: fixture shared a mutable `after_spot` object between successive fills, so an adversarial mutation tripped `C149_FILL_BALANCE` instead of the expected `C149_FILL_CHAIN`. This was a **test fixture alias**, not an economic or model result. Fixed by deep-copying each fill's before/after state; Action **39941785062** completed **44/44** tests green.
- C158 published the independent C148 full-TRAIN scorecard, a 15,864-hour-per-scenario synthetic 5-fold/6-regime regression, and a source-only workflow. Action **39941936444** completed **49/49** tests green. Current code head: `8a6a7936166050b6edad9e367ed165342789b1e1`.
- GitHub compare from the cycle base to C158 head: exactly **seven additive files** (3 verification modules, 2 tests, 2 workflows); **no changes** to Frozen V16, Frozen V99, legacy champion, paper/results, old research results, or any strategy threshold.

## What these tests establish — and do not
- C157 independently reconstructs declared hourly cash/positions, perp variation margin, modeled settled funding, scenario-specific stress fees, fee booking, NAV and summary proofs; it also rejects inherited balanced spot/perp inventory and pre-decision activity.
- C158 checks the fixed **15,864 TRAIN hours**, **654 daily decisions**, **five chronological folds** of **3,172/3,173/3,173/3,173/3,173 hours**, and requires identical exogenous market/funding inputs across severe/supersevere paths. It reports tail concentration, max drawdown, gross passive benchmark diagnostics and 3x2 regime coverage.
- The C158 fixture is intentionally **flat synthetic cash**: 0/5 positive model folds in both scenarios, only **1/6 regimes**, zero modeled market alpha. These are **test-fixture diagnostics, not historical TRAIN returns or rejection of the actual D1 architecture**.
- C157 trade tests use exactly **two artificial fills per scenario** after 168 hours of flat warmup, not exchange fills. C149/C150 and C148 do **not** authenticate OKX market data, fee tiers, settled funding, historical instrument specs, fills, or economic ROI.
- The separate first-party OKX collector Action **39935901175** completed on 2026-10-23 and has prospective artifacts; a successful collector does not by itself provide D1's complete historical 2021-12-09 to 2023-10-01 first-party execution/funding evidence.

## Scientific gate and next critical path
1. Additively integrate remaining local C152 model journal/feature/funding binding modules, then wire **C150 accounting + C148 risk + C151 native-lot checks** into one complete TRAIN-only, two-scenario execution with independent re-execution. Preserve preregistered D1 rules and source checks.
2. Obtain independently authenticated first-party historical BTC/ETH OKX spot+swap paired hourly prices, **historically as-of** instrument/fee tiers, **actual settled funding**, and execution/fill evidence. Labels, synthetic fixtures, CI success, and hashes without external trust anchors are insufficient.
3. Only then execute the preregistered D1 **economic TRAIN** with native fills and severe/supersevere shocks, five-fold robustness, six regimes, tails/DD, executable lots, benchmarks and independent accounting. Freeze a genuinely passing new candidate before accessing sealed validation `[2023-10-01, 2024-01-18)`. Final holdout `>=2024-01-18` remains sealed.

**C1 and C2 permanently rejected; no C1 retune. No promotion, no ROI, no orders.**
