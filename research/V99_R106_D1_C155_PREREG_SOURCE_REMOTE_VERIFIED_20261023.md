# V99 R106 D1 C155 — preregistered engine source staged and verified (2026-10-23 BRT)

**DATA_ONLY/HOLD — NO PROMOTION. No authenticated historical TRAIN ROI, no orders, no sealed validation, no final holdout.**

## Remote changes
- Branch: `research/v99-r106-native-all-regime-engine`.
- Starting head: `983502867d88b8e021bdb37575e61a41835669e7`.
- C155 head before this note: `5ff0d5586895b6a9913797f0aebf61da0fb2a1e0`.
- Exactly three additive files compared with the starting head:
  - `research/tools/v99_r106_d1_basis_carry_preregistered.py` (original C152 staged engine, Git blob `326595584f7a8c0f708e98286e3bf173fbe0622a`).
  - `research/tests/test_v99_r106_d1_c155_prereg_source.py` (8 new source-only causal regression tests, Git blob `853594121881fc0cd500be4b9db6e7ce42344591`).
  - `.github/workflows/v99-r106-d1-c155-prereg-source.yml` (read-only CI).
- Both deployed Python files' Git blob SHA-1 values independently matched the local originals exactly.
- No frozen, paper/results, legacy champion, historical data, or old research artifacts modified.

## Actual CI and local evidence
- GitHub Actions **39927941027**: `completed / success`, job **120328834430**, original job logs read.
- GitHub: **8/8** new prereg/causality tests and **17/17** existing exact-lattice/calendar tests passed; explicit `DATA_ONLY/HOLD — NO PROMOTION` assertion passed. **25/25 remote source-only tests**.
- Local C153 bundle with C155 test added: **143 tests run, 1 skipped, 0 failures**. The local suite is larger than CI; no economic data were used.
- C155 source-only tests verify severe/supersevere can make different cash/exposure decisions, t-1 causal boundaries, sealed TRAIN_END refusal, exact preregistered cost scenario acceptance, native funding instrument identity and settlement cadence, and non-authentication of self-reported OKX labels.
- **No real exchange data, historical ROI, independent five-fold severe/supersevere economics, authenticated fills, or native settled funding was produced.** A passing Action is not trading evidence.

## Explicit remaining blockers
1. The rest of the C152/C153 integrated source (execution, hourly account ledger, risk and independent oracle) is **not yet deployed**; only the original prereg engine and C153 lot verifier are remote.
2. Exact complete TRAIN coverage (15,864 hourly rows per asset), five chronological folds and six market regimes must be verified against actual first-party BTC/ETH spot/perpetual history. Self-reported `source='OKX'` is not provenance.
3. Historical as-of instrument lot/contract terms, account-native fee tiers, position-specific settled funding and original execution/fill evidence remain unverified.
4. A model with zero trades in supersevere or only one observed synthetic regime cannot pass economic robustness based on synthetic data.
5. Sealed validation [2023-10-01, 2024-01-18) and final holdout >=2024-01-18 remain unopened. C1 and other previously rejected candidates remain rejected without retuning.

## Next justified action
Stage the remaining C152 engine and independent oracles in additive batches with exact blob checks; run remote full integrated **synthetic-only** source CI, then bind original as-of exchange receipts to the complete TRAIN partition. Evaluate severe/supersevere economics and five folds **only** after source provenance and execution policy gates; otherwise remain DATA_ONLY/HOLD. Never trade, promote, invent ROI or touch Frozen/paper/legacy.
