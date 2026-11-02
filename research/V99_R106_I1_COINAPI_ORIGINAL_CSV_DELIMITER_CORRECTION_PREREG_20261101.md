# V99 I1 — original CoinAPI CSV delimiter contract correction (preregistered 2026-11-01 21:xx BRT)

**Source parser correctness only. NO licensed source, NO economic TRAIN, NO promotion, NO orders.**

## Evidence and failure mode, before changing code

CoinAPI's official [Quotes Flat Files schema](https://www.coinapi.io/products/flat-files/docs/datasets/quotes) explicitly prints a **comma-separated** CSV header and rows (`id_site_coinapi,time_exchange,time_coinapi,ask_px,ask_sx,bid_px,bid_sx`). Current `research/tools/v99_r106_i1_coinapi_quote_intake.py` incorrectly uses `csv.DictReader(..., delimiter=";")`. Its existing tests also fabricate semicolon-separated CSV, so they all pass while a correctly formatted licensed vendor file is rejected with `WRONG_COINAPI_QUOTES_COLUMNS`. This is a **real deterministic adapter incompatibility**, not a claim that the archive is available or that I1 makes money.

## Exact ex-ante correction and controls

1. Change only the original CoinAPI quote reader to standard comma CSV. Keep exact seven-column order, streaming gzip-to-EOF, original SHA256 twice, original S3 key, license-document digest, original exchange/arrival clock and causal/partition checks. No semicolon fallback; vendor source schema must not be guessed.
2. Update existing source fixtures to **comma**. Add explicit regression accepting the exact official CSV header/example shape (with valid TRAIN timestamps), and rejecting old semicolon fixtures and malformed/mixed delimiters. Maintain negative controls for truncation, source mutation, invalid size, crossed books, out-of-order clocks, wrong symbol, unlicensed file and sealed dates.
3. Run push-triggered GitHub Actions for the quote-intake source contract, inspect actual result. Passing software controls is **FORMAT_ONLY** and does not certify quote presence, completeness, original exchange clock, native Deribit contract units, account fee tier, settlement, margin, liquidity or any 5-fold severe/supersevere economic result.

**Hard boundary:** no modification to C1 or rejected strategies, original I1 decisions, V16/V99 Frozen, legacy champion, paper/results, public dashboard, validation >=2023-10-01, final holdout >=2024-01-18. Existing 658/661 missing original days and 0/180 economically certified lifecycles remain until proven otherwise.
