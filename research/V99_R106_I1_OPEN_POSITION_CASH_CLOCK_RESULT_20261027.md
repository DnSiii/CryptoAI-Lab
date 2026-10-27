# V99 I1 — verified open-position cash-clock correction, 2026-10-27

**Decision: SOURCE_ONLY/HOLD — NO PROMOTION.** No economic TRAIN, certified return, paper execution or orders.

## Material defect and correction

The previous fixture I1 decision adapter could return `CASH_NO_ELIGIBLE_SOURCE_OR_SIGNAL` for a Monday while existing option positions were not marked at that decision time; it could also return cash for a decision earlier than the wallet's last event. This incorrectly represented an unchanged, unvalued portfolio as a valid cash decision.

Preregistered in `research/V99_R106_I1_OPEN_POSITION_CASH_CLOCK_PREREG_20261027.md` at commit `da13ef7` before implementation. Implemented a strict time-reversal veto and full same-clock mark/NAV maintenance gate for every open position, including no-signal/no-new-entry cash decisions. Independently reproduced this gate without primary accounting imports, with a multiweek Monday-to-Monday mark and both severe/supersevere modeled cost paths. The fixed strategy rules and risk parameters were not retuned.

Implementation commits: `b0954b2`, `c51295d`, `6f7c5a5`. Independent GitHub compare from prereg shows changes to exactly three files: primary fixed bridge, independent oracle and tests; no Frozen, paper, champion, holdout, or legacy files.

## Actual CI and original-byte veto

[Actions 40457016921](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40457016921): **SUCCESS**, 19/19 deterministic tests including two-scenario multiweek CASH, missing/stale marks, and reversed decision clock. The same workflow independently restored original archived partial quote receipts and the original causal signal; **182 original decisions, 132 positive signals, 0 synchronized tradable source pairs, 0 certified complete lifecycles**. Independent original-byte oracle returned `INDEPENDENT_ORIGINAL_SIGNAL_AND_OPTION_BYTES_RECONCILED` and rejected forged intersections/source SHA.

These are software and partial-source controls, **not** a historical economic backtest. The missing full licensed 2021–2023 BTC/ETH executable options quote/size lifecycle and historical original native fee/margin/delivery terms remain the critical external blocker. A Tardis historical entitlement plus `TARDIS_API_KEY`, or a fully verified equivalent vendor archive, is required. Never infer profitability from this CI.

**Next justified step:** integrate a legitimately authenticated full source and native terms into the complete weekly coin-portfolio runner; independently replay all five chronological TRAIN folds, 3x2 regimes, severe/supersevere, tails, max DD and benchmarks before considering any sealed validation. Until then, keep SOURCE_ONLY/HOLD.