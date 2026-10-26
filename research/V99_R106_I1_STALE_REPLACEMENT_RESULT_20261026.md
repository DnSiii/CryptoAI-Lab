# V99 I1 — fail-closed last-arrival stale-event replacement (2026-10-26 12:50 BRT)

**Decision: SOURCE_ONLY/HOLD — NO PROMOTION.** This corrects a concrete as-of original quote selection false-positive. It does not deliver economic TRAIN or certify an executable options engine.

## Defect and fixed invariant
Previously the original source join and its independent oracle **discarded exchange-event-stale updates before selecting the latest physical arrival**. A new quote arriving 5 seconds before decision with a 600-second-old event could be skipped, allowing an older 20-second-old valid quote to survive as if still current. The result could falsely mark a two-leg book as available. Both primary and independent implementations had this flaw, so their agreement was insufficient.

Preregistered before code in `research/V99_R106_I1_STALE_REPLACEMENT_FAIL_CLOSED_PREREG_20261026.md` (commit `1a943d0`). Both now select the last **predecision** physical update per exact contract, with capture-order tie breaking, **then** apply five-minute event/arrival freshness, quote validity and synchronized distinct-strike rules. Crossed, stale-event or otherwise invalid newer quotes revoke older ones; postdecision updates cannot.

## Executed evidence
- GitHub Actions [40353191684](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40353191684), head `7059a9b`: **SUCCESS**. Nine preregistered synthetic adversarial cases passed against both primary and independent implementations, including the exact stale-event false-positive, equal-arrival last capture, crossed replacement and future-arrival nonrevocation.
- Original OKX spot + Deribit DVOL receipts independently recomputed **182/182** TRAIN causal signal rows and matched archived JSON; original 4,000 Deribit option quote sample rows rejoined and independently reparsed. Result unchanged: **132** positive variance indications, **0/182** synchronized original two-leg source-ready asset-weeks, **0** signal/source intersections, **0** certified full option lifecycles. No ROI.
- The independent oracle rejected forged intersection and source manifest SHA. Two earlier push-triggered runs [40353059603](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40353059603) and [40353066999](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40353066999) failed due to a shallow-checkout preregistration ancestry check, **not** market economics; the workflow was fixed to check the current precommitted SHA and rerun successfully.
- Independent compare `08fa2cd..7059a9b`: exactly **5 commits**, affecting only the preregistration, primary join, independent oracle, adversarial test and CI workflow. No Frozen, paper/results, champion, public dashboard, validation, holdout or order path modified.

## Remaining critical path
Actual authenticated, licensed 2021-12-09..2023-09-30 original BTC+ETH Deribit options BBO/size with venue+arrival clocks through every 21–45d entry/mark/exit lifecycle, documented contract units and dated account-specific native fee tier, margin/maintenance/liquidation and settlement index/TWAP receipts remain missing. GitHub Actions has no proven Tardis/CoinAPI entitlement. Alternatives: explicit Tardis Business/full-history grant, licensed CoinAPI original flat files or equivalent verified Amberdata archive with identical fields and continuity. Supplier entitlement and original bytes must be verified **before** a genuine integrated economic TRAIN on 5 chronological folds, 3x2 regimes, severe/supersevere, tails, drawdown, benchmarks and independent accounting. The validation window [2023-10-01, 2024-01-18) and final holdout >=2024-01-18 remain sealed.

**No orders, no authenticated fills, no ROI, no promotion.**
