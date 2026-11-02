# V99 I1 CoinAPI original quote schema and 100ns clock compatibility — preregistration (2026-11-01 22:5x BRT)

## Discovery and scope
The official CoinAPI Quotes *dataset* guide shows comma-delimited CSV, while the same provider's *downloadable data samples* page shows semicolon-delimited Quotes rows, including an options sample. Both show identical seven columns. The samples also contain seven fractional timestamp digits with a nonzero seventh digit (100-nanosecond precision). Current adapter accepts only comma and rejects nonzero seventh-digit timestamps, so it can reject vendor-original bytes even after lawful acquisition. Sources:
- https://www.coinapi.io/products/flat-files/docs/datasets/quotes
- https://www.coinapi.io/products/flat-files/docs/data-samples/quotes
- https://www.coinapi.io/products/flat-files/docs (standard time output yyyy-MM-ddTHH:mm:ss.fffffffZ)

## Fixed implementation before any result
1. Recognize exactly the two explicitly documented delimiter dialects from the exact seven-field header; reject mixed rows, extra/missing fields, other delimiters, duplicate/malformed headers. Never guess or silently skip rows.
2. Preserve original 100ns clock ordering and exchange<=arrival causal relation with integer ticks; retain legacy microsecond metadata as floored *display only* and expose exact first/last 100ns ticks. Reject nonzero precision beyond 100ns; no float timestamp arithmetic for fractional part.
3. Adversarial synthetic tests: both documented dialects; nonzero seventh digit; same-microsecond different-tick causal reversal; mixed dialect; >7-digit nonzero; original SHA preserved; source and sealed TRAIN guards unchanged.
4. Run real GitHub CI, inspect results. Do not claim original historical coverage, native fees, fills, TRAIN ROI, freeze, validation, holdout, or promotion.

## Immutable boundaries
Only CoinAPI source intake/tests and their prereg/result docs may change. Do not modify frozen, paper, champion, sealed validation or holdout. No orders or historical claims. Existing external credential/archive block remains.
