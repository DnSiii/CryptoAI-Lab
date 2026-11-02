# V99 I1 — Original OPEN / ex-ante signal binding result (2026-11-02)

## Change and verification

Branch: `research/v99-r106-native-all-regime-engine`. Preregistered at `aeaa2c7f03fe822316c369a38fd1049024f3acaf`, then implementation `c5bd115a02decfa37580074dc5d5b8abbaf649c9`, regression tests `607876691e980766cbc3906377de7f22a212be1d`.

A real internal source-integrity gap was closed: an OPEN could previously be reported as matching an original CoinAPI option book without proving that the OPEN belonged to a positive, immutable, ex-ante causal signal. The helper now validates all 180 scheduled TRAIN decision keys, chronological folds and allowed signal labels; each scenario OPEN must contain the exact source-bound signal object and a `POSITIVE_EX_ANTE_PREMIUM` label. Scenario-specific risk vetoes may legitimately produce different OPEN counts. This is an integrity gate, not a new strategy or return estimate.

Final GitHub Actions run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41532354629 — **SUCCESS**, 18/18 synthetic tests, including 4 new adversarial regressions (forged signal, nonpositive source signal, missing signal receipt, and altered fold). The earlier intermediate implementation-only run https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41532329548 failed before fixtures were updated; final HEAD run passed. CI also verified the nonfixture economic source gate remains **`SOURCE_HOLD: WRITTEN_COINAPI_CHAIN_LICENSE_REQUIRED`**. Independent changed-file comparison from prior HEAD `312965324272da1a13d65591c1c3f32e3cc7f0a2` shows only this prereg, the CoinAPI source bridge, and its regression tests were changed before this result document.

## Decision: SOURCE HOLD — NO PROMOTION

No original 661-day licensed option quote/size tape was supplied; no independently authenticated historical native account fee tier, size-unit conversion, margin/liquidation, settlement index/delivery or execution fills were supplied. No original option economic TRAIN was run. **0/180 original complete option lifecycles economically certified (last audited count)**; no independently certified ROI, profitable folds, or authorization to freeze/promote. Neither successful synthetic CI nor source parity proves exchange-native PnL.

Next critical step is procurement and independent receipt validation of full 2021-12-09..2023-09-30 BTC/ETH original two-sided option market data and dated native terms. A lawful alternative provider may be used only if the same coverage, integrity, native contract-size semantics, and execution/funding provenance are demonstrably verified. Once those exist, perform complete fixed TRAIN with scenario-specific severe/supersevere accounting and independent replay; only then consider gates and sealed validation. The separate 2023-10-01 onward validation, final holdout, Frozen, paper, champion and orders remain untouched.
