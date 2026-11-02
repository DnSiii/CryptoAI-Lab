# V99 I1 — CoinAPI official CSV original-source adapter repair: verified result (2026-11-01 ~21:44 BRT)

**SOURCE FORMAT FIXED / ECONOMIC TRAIN BLOCKED / NO PROMOTION / NO ORDERS.**

## Evidence-backed root cause

Official [CoinAPI Flat Files Quotes documentation](https://www.coinapi.io/products/flat-files/docs/datasets/quotes) explicitly uses **comma-separated** header and quote rows. The prior intake parser was hard-coded to `csv.DictReader(... delimiter=";")` and all prior fixtures used semicolons. Consequently, a correctly formatted vendor original gzip would fail at `WRONG_COINAPI_QUOTES_COLUMNS` even if a legitimate 2022 quote archive were delivered. This is a deterministic source-to-engine compatibility bug, independently established from the provider's published schema, **not** an observed licensed original file.

## Execution and independent checks

- Pre-registered root cause and no-retune constraints: [4c4be39](https://github.com/DnSiii/CryptoAI-Lab/commit/4c4be39fae0b34f17878d2aa89c293fe37c7105a).
- Changed only CoinAPI source reader to comma CSV (no permissive fallback): [be9a56e](https://github.com/DnSiii/CryptoAI-Lab/commit/be9a56e95fbc21fd7cf3157e3d8ea2753513750b).
- Replaced semicolon-only fixtures with official comma format and added positive official-schema, negative old-semicolon and mixed-format controls: [f42cc77](https://github.com/DnSiii/CryptoAI-Lab/commit/f42cc77248ffc09690df098bb185d4a751fb2350).
- Real push-triggered [GitHub Actions 41368707411](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41368707411): **SUCCESS, 22/22 source-adapter tests**, including streamed 25,000-row gzip, SHA256 preservation, license-document digest, causality, invalid original S3 key, wrong venue, sealed partition, truncated gzip, bad depth, crossed quote, out-of-order clock. Prior intermediate [41368697681](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41368697681) **failed as expected** after the reader changed but before legacy semicolon fixtures were updated; the final workflow passed.
- Independent repository compare `3a4035b..f42cc77`: **exactly 3 files** changed (preregistration, quote reader, source contract tests). No Frozen, champion, paper/results, validation, final holdout, engine signals or execution rules touched.

## Still blocking actual delivery

No authenticated `COINAPI_API_KEY` or lawfully licensed historical Deribit BTC+ETH original quote files were supplied. Last provider inventory [Actions 41363988430](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41363988430) returned `BLOCKED_NO_COINAPI_API_KEY`, 0 remote pages and 0 original objects. A valid source requires a provider-granted key with usage credits and written retention/replay rights, exact original quote/size files for fixed 2022-01-23 and then all 661 TRAIN days/lifecycles; dated venue/account native fees, lot units, margin/liquidation and settlement terms remain separately required. Historical hypothetical fills must be modeled conservatively, never described as actual fills.

**Current qualified status:** 658/661 original days absent, **0/180 complete economically certified option lifecycles**, no 5-fold original severe/supersevere TRAIN, no independently validated ROI. 2023-10-01 onward remains sealed. V16/V99 Frozen, champion, paper and public dashboard unchanged. **SOURCE HOLD — NO PROMOTION.**
