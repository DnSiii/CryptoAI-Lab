# V99 R106 — ex-ante partial quote execution-friction feasibility (2026-10-24)

**Pre-registration before running code. DATA_ONLY/HOLD, NO PROMOTION.** No trading candidate, ROI, actual fill, validation or holdout access. Immutable V16/V99 Frozen, paper and champion are out of scope.

## Fixed question
Do the **existing** two bounded third-party Tardis Deribit quote samples show observable, two-sided, non-crossed bid/ask quotes with positive displayed size and plausible source/arrival timestamps, and what are their *observed* one-crossing relative spreads? This is a cost *lower bound*, not an executable backtest. It is not a new alpha grid and does not resolve full-history entitlement.

## Frozen input and formulas
Only `tardis_quote_probe/deribit_options_quotes_2022-01-01.csv` and `...2023-01-01.csv`, each capped at 2,000 consecutive first rows and bound to existing SHA256 manifest. For each row, classify numeric/non-numeric, non-positive sizes/prices, locked/crossed quotes, timestamp availability and whether `exchange_timestamp <= local_timestamp`. For valid two-sided rows compute **one crossing** `10000*(ask-bid)/((ask+bid)/2)` basis points, not PnL; a same-instant buy-ask/sell-bid round trip costs this full spread before fees, hedges and price changes. Quantiles use sorted values with index `ceil(p*n)-1` for p=.50 and .90, computed per date and BTC/ETH symbol prefix; keep separate asset/date strata. The sample is strongly first-seconds-of-day biased, nonrepresentative of whole TRAIN. If timestamp skews exist, quarantine those rows from causal-use classification rather than treating them as clean.

## Independent check
A second implementation parses original CSV and manifest, recomputes valid rows, spread quantiles using `decimal.Decimal`, and compares count, p50, p90 and per-row source timing classification. Both scripts must fail on hash mismatch, unexpected date or missing fields. Never convert option premium to USD without original underlying reference and contract denomination, and never claim fills from quotes.

## Economic gate
Regardless of numeric spread result, `complete_train=false`, `native_fills_certified=false`, `economic_train_run=false`, `promotion=false`. The external blocker remains authenticated licensed full historical 2021-12-09..2023-09-30 L1/L2 quotes (bid/ask/size/exchange+arrival time), complete coverage/gaps, Deribit contract and settlement rules, native fees and size-aware fill/slippage evidence. Neither a passing CI nor narrow source sample can unlock any validation/holdout.

## Decision rule
Report actual sample friction with all limitations; continue work on independently verifiable economic mechanism only when input sufficiency permits. No posthoc parameter selection or retune of rejected C1/F1/G1/H1.
