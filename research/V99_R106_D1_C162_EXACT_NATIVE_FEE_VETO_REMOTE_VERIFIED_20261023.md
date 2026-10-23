# V99 R106 D1 C162 — original native-fee veto + exact independent TRAIN reexecution (2026-10-23 BRT)

**DATA_ONLY/HOLD — NO PROMOTION.** Source-only scientific integration; no authenticated historical economics, no orders, no paper/results update, no validation or final holdout.

## Executed and independently checked

- Published the original **C136 preregistered native-fee veto** implementation from the existing local C152 package as a new additive source file. No parameter change, C1/C2 retune, or economic candidate selection.
- Added C162 independent decision verifier. Replays **654 preregistered decision hours × 2 cost scenarios = 1,308 scenario decisions**, including **2,616 asset-scenario decision checks**, against exact C136 results and a separately reconstructed Decimal 2× full native+stress roundtrip hurdle.
- Negative controls: forged positive exposure, fee tier observed after t−1, missing decision hour, and cost-path swapping in a deliberately positive synthetic example. For a 24h forecast of 1.2% with synthetic spot/perp taker fees of 0.10%/0.05%, the severe hurdle is 1.16% and supersevere is 1.72%; severe permits the modeled pair and supersevere vetoes it. **This is a fabricated test input, NOT historical profit or evidence of D1 edge.**
- GitHub Actions **39973244534** completed **SUCCESS** on commit **56dc2956f1aef66ac238ce5a27b7bb0ed73ea047**. Job **120481128267** logs show **74/74 tests passed in 8.783 seconds**, and the no-promotion permission check passed. The local original C136 test suite independently passed **12/12**.
- Compare from C161 branch head **3b4fd3e** to CI commit **56dc295**: **four files added, zero existing files modified or deleted** (one workflow, one original C136 source, one C162 oracle, one C162 test). Protected V16/V99 Frozen, paper/results and legacy champion untouched.

## Remaining blockers (hard fail closed)

1. The test's source labels, 8-hour funding fixes and native fee tiers are **synthetic**. Self-declared OKX labels, successful Actions, SHA hashes and model accounting do not authenticate first-party historical BTC/ETH spot+perp execution, instrument lot rules, account-specific historical fee tiers, funding announcement availability, actual settled funding, or fill/slippage receipts.
2. C162 proves exact C136 fee-veto mechanics on the same full TRAIN grid, **not** independently authenticated exchange data, complete deployed C140 hourly journal or C146 feature/funding binding. The synthetic fixture covers only **1/6 regimes**, zero real trades, and cannot establish five positive real TRAIN folds or robust risk/benchmark gates.
3. C140–C147/C152 integrated source still needs additive deployment and independent remote tests; source-first integration should precede any economic run. If first-party provenance remains missing, do not produce ROI.
4. Validation [2023-10-01, 2024-01-18) and final holdout >= 2024-01-18 remain sealed. C1/C2 and prior archived alpha candidates remain rejected. Never tune to contaminated historical R106 holdout diagnostics.

## Next justified step

Additively deploy the C139 target-rebalance, C129 hourly accounting and C140 model-only journal dependencies from the already prepared C152 package; then integrate the C141–C147 exact decision/funding/feature oracles, execute GitHub source CI and independent replay. Separately bind original OKX historical paired spot/perp, funding, native fee tier, lot and fill receipts. Only after the external provenance gate passes run the one preregistered D1 historical TRAIN with five chronological folds, severe/supersevere, six regimes, tail/DD and four passive benchmarks. Never infer performance from the synthetic test.

**NO PROMOTION.**
