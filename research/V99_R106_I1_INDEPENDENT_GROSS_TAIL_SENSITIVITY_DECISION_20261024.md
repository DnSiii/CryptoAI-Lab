# V99 R106 I1 — independent gross variance tail sensitivity, economic execution still blocked (2026-10-24 BRT)

**DATA_ONLY/HOLD — NO PROMOTION.** This is a **post-screen descriptive stress diagnostic** on the existing I1 30 original nonoverlapping BTC/ETH TRAIN asset-windows. It is **not** a preregistered alpha gate, options PnL, economic backtest, full engine, evidence of executable quotes, a formal strategy rejection or a reason to open validation/holdout.

## Reproducible execution
- Protocol committed first: `5a8e94d86f31d1d74e4a1ce69c0b0ff706468367`. Implementation `research/tools/v99_r106_i1_gross_tail.py`; independent Decimal verifier `research/verification/independent_v99_r106_i1_gross_tail_oracle.py`; new read-only Actions workflow `.github/workflows/v99-r106-i1-gross-tail-stress.yml`.
- [Actions 40091478772](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40091478772) **SUCCESS**. Restored original I1 report (Actions 40087572354), original first-party OKX hourly TRAIN opens (Actions 40019588739), and original first-party Deribit DVOL TRAIN (Actions 40072202459). Independently reconstructed the original 30 source-to-premium observations, reexecuted 1.0x/1.25x/1.5x realized-variance sensitivities using Decimal, verified the original SHA and rejected an intentionally corrupted stress metric.
- Exactly 15 nonoverlapping 30-day windows per asset, 3 per each of 5 chronological TRAIN folds. No new window selection, parameter fitting, orders, fees, fills, capital or NAV.

## Gross dimensionless variance differences — NOT returns or PnL

| Counterfactual realized-variance multiplier | BTC mean gross variance premium | BTC positive folds | ETH mean gross variance premium | ETH positive folds |
| --- | ---: | ---: | ---: | ---: |
| 1.00x observed | +0.01170168 | 4/5 | +0.00934878 | 4/5 |
| 1.25x | +0.00442164 | 3/5 | **-0.00271750** | 3/5 |
| 1.50x | **-0.00285841** | 3/5 | **-0.01478378** | 2/5 |

Worst single original/stressed window gross variance premiums:
- BTC 1.0x **-0.02680017**, 1.25x **-0.04123158**, 1.50x **-0.05566298**.
- ETH 1.0x **-0.06381062**, 1.25x **-0.09809369**, 1.50x **-0.13237676**.

These 25%/50% amplifications are **counterfactual risk sensitivities**, not severe/supersevere trading cost scenarios, a calibrated probability distribution, observed future returns, or tradable profits/losses. BTC and ETH are correlated; 15 observations per asset are too few to certify robust tail performance. This sensitivity materially weakens the economic case for paying for an unverified full options archive based on the I1 structural PASS alone, but **does not invalidate or change the original structural screen**.

## Critical path and decision
**Do not** spend on licensed options history without a verified provider proposal covering both BTC and ETH **2021-12-09 through 2023-09-30** with point-in-time bid/ask, displayed sizes, exchange and local arrival timestamps, strike/expiry/instrument identifiers, complete coverage/gap manifest, historical contract/margin/settlement rules, historical account fee terms, and hedge/funding/slippage inputs. Public first-seconds-of-two-days sample and non-sample HTTP 403 remain insufficient. Any future delta-hedged short-variance options engine requires full cash/collateral/margin, bid/ask execution, risk/tail, independent accounting and five-fold TRAIN **before** formal freeze and validation. A conservative modeled fill is not an authenticated hypothetical exchange fill.

**Next engineering priority:** avoid another serial posthoc strategy; seek one economically distinct, explicitly preregistered complete architecture supported by already complete native TRAIN data and cost/funding provenance, or resolve the precise option archive entitlement. No validation [2023-10-01,2024-01-18), final holdout >=2024-01-18, V16/V99 Frozen, legacy champion, paper/results, dashboard promotion or live orders were touched. **NO PROMOTION.**
