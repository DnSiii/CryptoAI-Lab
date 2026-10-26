# V99 I1 — fail-closed coin-account mark integrity, 2026-10-26 06:23 BRT

**Decision: SOURCE_ONLY/HOLD — NO PROMOTION.** No historical economic TRAIN, no proven ROI, no orders, no validation/holdout access, no Frozen/paper/champion edits.

## Actual work and causal evidence
- Precommitted precise falsification and fix BEFORE code in `V99_R106_I1_MARK_INTEGRITY_FAIL_CLOSED_PREREG_20261026.md` (commit `7d22b3c`).
- Repaired production `Wallet.check` so reconstructed negative coin liabilities, zero/negative underlying marks, boolean/future mark timestamps, and invalid position quantities/strikes/margin/expiry fail closed (commit `ff1a627`). A forged negative mark could otherwise inflate native NAV and evade maintenance, a material safety false positive.
- Independently repaired the separate Decimal reference oracle to reject negative exit fees/slippage and nonpositive mark index (commit `8b8d867`). Added four adversarial test methods (commit `104c421`).
- [GitHub Actions 40299134588](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40299134588), final source `104c421cc3f85c92763b94b86365720614e48c1d`: **completed SUCCESS, 18/18 deterministic synthetic tests passed**. Independent severe and supersevere journals each reconciled **8 events, 2 positions and 1 NAV**; these are software tests, not exchange fills or profits. Verified via actual workflow job logs.
- Independent commit comparison `812fdac...104c421`: exactly four research-only files changed (prereg, ledger, reference oracle, tests). No Frozen, paper/results, champion, dashboard performance, or holdout changes.

## Still blocking a complete, executable I1 economic TRAIN
The authenticated original BTC **and** ETH 2021-12-09..2023-09-30 Deribit options BBO+sizes and both venue/arrival clocks for complete entry/mark/exit/settlement lifecycles are not available; **0/182 certified asset-week lifecycles**. Original native lot/unit conversions, account-specific historical fees, delivery indices, dated maintenance/liquidation margin and legal entitlement also remain unproven. Tardis full-history entitlement or an independently verified CoinAPI/Amberdata equivalent with original bytes and source hashes is required. Synthetic integrity CI cannot substitute for these market receipts.

Next material step: obtain authorized complete source+native terms; run source-to-ledger integration on TRAIN only, five chronological folds, 3x2 regimes, severe/supersevere, independent economic replay and preregistered gates. Do not open validation [2023-10-01,2024-01-18) or final holdout >=2024-01-18 unless legitimate new candidate passes TRAIN and is frozen. No C1 retune.
