# V99 R106 I1 — independent five-fold uncertainty and historical options source decision (2026-10-24 BRT)

**DATA_ONLY/HOLD — NO PROMOTION.** This is a post-screen *descriptive* uncertainty check of the existing original first-party I1 30 gross variance observations. It is **not** an options execution backtest, account PnL, a new alpha experiment, a rejection of the original structural PASS, or permission to open validation/holdout.

## Verified real execution and immutable evidence
- Protocol preregistered at commit `7d7a8f385f27ca0f13b793574502597fce4cbb50`, before implementing this audit; fixed one-sided 5-fold sign-test and leave-one-fold-out formulas, no feature or threshold grid.
- Code `research/tools/v99_r106_i1_fold_uncertainty.py`, separately implemented Decimal oracle `research/verification/independent_v99_r106_i1_fold_uncertainty_oracle.py`; read-only workflow `.github/workflows/v99-r106-i1-fold-uncertainty.yml`.
- [Actions 40095787802](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40095787802) **SUCCESS**: restored original source-verified I1 TRAIN artifact from [Actions 40087572354](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40087572354), verified 30 original rows and 15 paired nonoverlapping decision windows, five chronological folds, recomputed independently with Decimal, rejected a deliberately corrupted metric, archived JSON outputs. No future market data parsed, no trading/ROI computed.

## Gross variance differences (dimensionless; NOT option PnL)

| Fixed original metric | BTC | ETH | Equal-weight BTC/ETH paired observation, NOT portfolio |
|---|---:|---:|---:|
| Positive TRAIN folds | 4/5 | 4/5 | 4/5 |
| Equal-fold gross mean | +0.01170168 | +0.00934878 | +0.01052523 |
| Idealized one-sided 5-fold sign-test tail | 0.1875 | 0.1875 | 0.1875 |
| Lowest leave-one-fold-out mean | +0.00582969 | **−0.00179192** | +0.00201889 |
| Largest positive fold's share of positive fold means | 57.23% | **70.74%** | 64.71% |

The sign-tail 6/32 = 0.1875 is exact **only under a hypothetical independent symmetric five-fold null**. Folds are sequential and BTC/ETH are correlated, so it is not an independently calibrated real-world p-value; combining asset tails would be invalid. A positive gross variance difference does not establish an executable risk premium after option spreads, hedge costs, financing, liquidation or severe tails. In particular, ETH's sign changes when the strongest fold is omitted, showing concentration. Prior independent [gross tail sensitivity 40091478772](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40091478772) already found negative ETH mean at 1.25x realized variance and negative BTC/ETH means at 1.50x; those are counterfactual variance sensitivities, **not modeled trading costs**.

## Historical quote entitlement — precise external blocker and an alternative that does NOT solve it

The Tardis first-of-month Deribit samples are public, but **non-sample original historical quote requests returned HTTP 403** in [Actions 40083504198](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40083504198). The required artifact is an **authorized 2021-12-09 to 2023-09-30, BTC and ETH, time-stamped point-in-time option best bid/ask plus displayed sizes, exchange and local arrival timestamps, instrument/expiry/strike and gaps manifest**, historical contract/settlement/margin specifications, native account fee tier and hedge/financing assumptions. Trade prints or IV candles alone are not executable bid/ask evidence.

**Alternative investigated (not purchased):** [Volar's official historical-data page](https://www.volardata.com/) advertises dense **BTC-only** Deribit option history June 2021–September 2024, with full BTC history available on a **€990 annual** tier, while its historical **ETH** chain is absent for the required TRAIN. [Its published 23-column schema](https://app.volardata.com/schema/chains) includes bid/ask *prices* but **does not list displayed bid/ask sizes or a separate local receive timestamp**. Its historical `mark_price` was vendor-derived and reportedly repaired in October 2026; marks cannot substitute for original executable fills. Thus even a BTC-only licensed archive would require contractual size/arrival evidence, gap manifests, and a separately preregistered BTC-only architecture; it cannot validate the existing BTC+ETH I1 design. **Do not buy any subscription on this evidence.** Other suppliers may be evaluated only after verifying the exact instrument/time/field coverage and license.

## Decision and next real work
**No source purchase authorized; do not claim a validated V99.** I1 remains a gross structural screen only, with insufficient independent evidence to prioritize paid data acquisition over a source-complete distinct mechanism. Stop spending cycles re-testing its gross IV feature. Next justified work is to select a fundamentally distinct causal economic mechanism whose **actual** trading cashflows are supported by the existing complete original TRAIN market data, preregister fixed complete-system rules and costs before any returns, run all five folds with full accounting, severe/supersevere and 3x2 regimes, and independently verify. If options are chosen instead, the external entitlement and historical execution metadata above must be supplied first.

No orders, V16 Frozen, V99 Frozen, paper-results, legacy champion, public dashboard promotion, sealed validation [2023-10-01,2024-01-18), or final holdout >=2024-01-18 were touched. **NO PROMOTION.**
