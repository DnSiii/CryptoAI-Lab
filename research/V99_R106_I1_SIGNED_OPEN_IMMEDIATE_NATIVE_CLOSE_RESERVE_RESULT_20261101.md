# V99 I1 signed OPEN immediate native-close reserve — verified result (2026-11-01)

## Scope and preregistration
Preregistered before implementation at commit `46a2ba7581c2bffb98ecd35e71a895d7d5ebd9c6`. This is a risk/accounting integrity correction, not a new alpha or economic TRAIN. Branch `research/v99-r106-native-all-regime-engine`, final verified code SHA `7544213807d1d4d19827ee5ce39d695bcb19fd27`.

## Fixed and independently reexecuted
On signed nonfixture OPEN, the original source-bound two-sided short/long executable quote and signed dated account fee schedule now yield an independent hypothetical immediate-close fee (the existing MARK fee formula). A separate no-production-import Decimal oracle verifies each leg and total before wallet mutation. The postentry maintenance veto reserves the greater of severe/supersevere modeled exit fee and this independently verified historical-native *hypothetical* close fee, plus modeled slippage and adverse executable close liability. A hypothetical close is NOT an actual fill.

Adversarial synthetic boundary: 1.04 coin starting collateral, 1 native lot, 0.01 coin entry fee, 0.0024 slip, short ask 0.09, long bid 0.04, 1 coin maintenance. Old modeled exit fee 0.0024 would have left 1.0028 coin against maintenance 1. New native close fee 0.01 leaves 0.9952 coin and correctly VETOES the OPEN; 1.05 coin starting collateral passes. Primary close-fee tampering is vetoed by the independent oracle. These are synthetic controlled examples, not historical economic returns.

## GitHub CI actually executed on final SHA
- [Native cost and original source gate Actions 41333758736](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41333758736): SUCCESS, seven suites 8+16+9+13+8+6+12 = **72/72** technical tests; original archived 182 signal observations, 132 positive, **0/182** original option source intersections; `BLOCKED_PARTIAL_ORIGINAL_OPTION_ARCHIVE`; zero certified lifecycles.
- [Dated native fee preflight Actions 41333758793](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41333758793): SUCCESS, six suites 16+9+8+8+13+6 = **60/60** technical tests, explicit 0/180 economic certification.
- Earlier intermediary CI failed because isolated synthetic cryptographic test harnesses mocked the dated fee function to return None. Corrected only those mocks to return the required fee evidence shape; production fail-closed behavior was not weakened.

## Decision and missing provenance
**SOURCE HOLD — NO PROMOTION.** No complete authenticated licensed 661-day original BTC/ETH options quote/size and lifecycle archive (658/661 days still missing); no independently authenticated historical account fee tier/lot/margin/liquidation terms, source-bound delivery indices, executable fill provenance or external auditor credentials. The alternatives are equivalent licensed original-byte archives plus original account-specific evidence, never synthetic assumptions. No full historical economic TRAIN, 5-fold severe/supersevere independent gates, frozen new candidate, validation or final holdout. 0/180 certified; no ROI, realized paper, orders or dashboard performance promotion. V16 Frozen, V99 Frozen, champion and paper remain untouched.
