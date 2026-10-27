# V99 I1 — native wallet position identity binding: executed result (2026-10-26 21:46 BRT)

## Real defect fixed, not alpha discovery
The native BTC/ETH coin wallet previously checked numeric short/long strike and expiry but **not their equality to the literal option contract IDs** stored in Position. A forged reconstructed Position could be marked using one pair of instrument IDs and settled using different numeric strikes/expiry. This breaks source-to-payoff accounting even with positive cash and valid numerical margin. The preregistration was committed first: `5ef0e0f45e52dd6bb2b99d24516aa47f93fb9e6d`.

## Exact implementation and falsification
- Source fix `662c63754a6aa99aafc6a475a12f526231aeeac1`: every Wallet.check parses both exact BTC/ETH Deribit PUT symbols, validates asset, 08:00 UTC expiry and exact decimal strikes against Position.high/low and expiry_ms; fail closed on malformed/non-string, wrong asset, call, expiry or either strike.
- Adversarial tests `70b33690d8c9ba15c30479350b7c8a0f1ebc5b1b`: nine distinct position forgery cases for each of severe and supersevere (18 mutated wallets); each rejected at wallet validation, NAV and atomic settlement entry guards. Unmodified positions remain valid.
- **Actual GitHub Actions** [40428418926](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40428418926), on exact test commit: **SUCCESS, 26/26 tests**; the new forged-identity test passed. The independent synthetic coin journal replay still MATCHes in both cost scenarios (7-event two-position and 9-event mixed-expiry accounting paths). No original market options tape was used.
- Compare `3c121da...70b33690`: changed only research docs, this wallet implementation and its tests. No sealed validation, final holdout, Frozen, paper, legacy champion or order routing touched.

## Formal decision
**ACCOUNTING_INTEGRITY_PATCH_ONLY / SOURCE_ONLY/HOLD — NO PROMOTION.** This removes a specific prospective source-to-settlement mismatch, not the economic dependency. 0/182 complete original 21–45-day BTC/ETH option lifecycles certified. No historical 5-fold TRAIN economic run, realized PnL, validated ROI, actual fills or trades. Next real step is original licensed 2021-12-09..2023-09-30 full Deribit option bid/ask+size+arrival tapes, verified native contract units, historical fees and margin/liquidation/delivery terms; then execute and independently replay severe/supersevere complete-system TRAIN before any freeze or sealed validation.
