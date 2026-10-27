# V99 I1 — immutable fold binding + invalid CASH wallet correction (2026-10-27 01:45 BRT)

**Decision: SOURCE_ONLY/HOLD — NO PROMOTION.** This is a research-only fixture correctness fix, not a full integrated economic engine, original fills, ROI, paper or trading permission.

## Changes and preregistration
- Precommitted exact acceptance rules in `research/V99_R106_I1_FOLD_AND_CASH_GUARD_PREREG_20261027.md`, commit `acbfe5285b9aa19fd4944caa62daf61dcf6a87af`, **before** code changes.
- Primary bridge commit `da6032dc5063b178395e31c66e20d76de03195a8`: decision fold must match the original 5 fixed chronological TRAIN boundaries, not merely be an integer 1..5. A no-trade/CASH decision must validate the existing wallet before returning.
- Independent oracle commit `32d299d29ec66ef39084ec9b0691bd54b9f571a3`: independently recomputes frozen fold boundaries and rejects invalid starting wallet cash/reserve, timestamp, initial coin, reserve/positions and mark identifiers.
- Adversarial tests commit `06e123fcdc9700df91ecdc97383f8cfce9f8d061`. Initial [Actions 40451325667](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40451325667) **failed 16/17** because an existing right-censor test moved the timestamp to September 2023 but left a January 2022 fold label. Corrected **only the test fixture** to fold 5 in commit `ad98f3c760ea22fb64fd18b7da5580c08625699f`; no strategy parameters or historical data changed.

## Final actual GitHub execution
[Actions 40451353844](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40451353844): **SUCCESS**, 17/17 deterministic tests, including wrong-fold and four invalid CASH wallet negative controls, both severe/supersevere modeled fixture paths. CI re-downloaded the original archived causal signals and partial Deribit sample, re-executed the original join and the independent original-byte oracle, and enforced the no-promotion gate.

**Original historical data:** 182 asset-week decisions, 132 original positive causal signals, **0 original synchronized two-leg source-ready asset-weeks, 0/182 complete certified option lifecycles**. The independent byte oracle rejected forged intersections and forged source SHA; neither test success nor a partial original sample establishes a tradable historical return.

Read-only GitHub diff from prior successful `b5565e7` to corrected `ad98f3c` shows only isolated bridge/oracle/test/prereg plus an already-existing prior-cycle result document. No V16 Frozen, V99 Frozen, paper/results, legacy champion or sealed validation/holdout files were changed by this work. No orders sent.

## Unresolved critical path
Original legally entitled Deribit BTC+ETH 2021-12-09..2023-09-30 options BBO/depth with venue/local arrival timestamps and complete 21–45d lifecycle, original fee tier, lot/margin/maintenance/liquidation, settlement/delivery index and independent provenance. GitHub `TARDIS_API_KEY` was absent in the last authenticated scope attempt; this cycle did not claim a new authenticated vendor query. An explicitly licensed Tardis full-history grant or a verified equivalent vendor archive could unblock acquisition, but access alone does not certify executable fills or profitability. Full integrated TRAIN, 5 folds, 3x2 regimes, severe/supersevere, tail/DD/benchmarks and independent economic replay remain **NOT RUN**; validation and holdout stay sealed.
