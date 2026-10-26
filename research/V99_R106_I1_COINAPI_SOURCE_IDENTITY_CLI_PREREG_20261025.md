# V99 I1 CoinAPI source identity and runnable intake correction — preregistered 2026-10-25 23:5x BRT

**SOURCE_ONLY/HOLD — NO PROMOTION.** This is a data-ingestion defect fix, not a strategy retune, historical option backtest or claim of licensed access.

Before changing the parser or its tests, the following fail-closed rules are fixed:

1. The current CLI hardcodes `licensed=False` and therefore rejects **every** actual file, even with an authorized archive. Replace with explicit `--license-document PATH --license-sha256 HEX --source-key ORIGINAL_S3_KEY`; the document must be a nonempty regular local file whose SHA-256 matches the independently provided expected digest. This is *operator-supplied evidence*, not independent proof of legal rights. No document means BLOCKED.
2. The quote CSV contains no instrument ID. Bind the declared BTC/ETH Deribit option to the original CoinAPI object key `T-QUOTES/D-YYYYMMDD/E-DERIBIT/IDDI-...+SC-...+S-EXCHANGE_SYMBOL.csv.gz`, and require the source key date and each quote arrival timestamp to be in the **same TRAIN partition**. Wrong venue, symbol, key, date, validation or holdout must be rejected. Original key remains a **claim** until authenticated S3 listing/bytes/manifest proves it.
3. Official CoinAPI schema says `id_site_coinapi` is a site UUID, but public samples sometimes leave it blank. Accept only empty or syntactically valid UUID; reject arbitrary strings. Never treat the site field as an instrument ID.
4. Existing positive bid/ask and sizes, strict original clock ordering, microsecond fail-closed rule and gzip SHA-256 remain. Add adversarial controls and run the GitHub workflow on the research branch. No changes to Frozen, paper/results, champion, validation, holdout or order paths.

Acceptance: independent synthetic tests must reject spoofed object keys, mismatched partitions, invalid site IDs and wrong document hashes; CLI must be runnable with a fixture document and original-key-shaped fixture. A green CI means **software intake only**. Real licensed full 2021–2023 BTC/ETH entry-through-exit BBO+size, native size-unit/fee/margin and independent economic replay remain required.

Official source format: https://www.coinapi.io/products/flat-files/docs/datasets/quotes and https://www.coinapi.io/products/flat-files/docs/data-samples/quotes .
