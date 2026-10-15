# V98 Independent — Phase265 CFTC release-availability gate (frozen preregistration)

Scope: `research/v98-independent-zero`, V98 Independent only. DATA ONLY: no crypto prices, PnL, strategy selection, 2026+ training, XRP, V14/V15/V99 or old Phase083 holdout.

Source: authenticated Phase264 CFTC CME BTC legacy futures-only contract 133741, 157 normalized weekly observations 2023–2025, exact SHA-256 `6b2a01f06db2b95c8eec97862730b61b7c6033692dc79e216472095707d8be7d`. Reject changed schema, source hash, contract, calendar, duplicate reports, negative fields, or open-interest accounting mismatch.

Availability rule frozen before economic testing: `max(report_asof+14 calendar days, officially documented delayed release+1 UTC day)`; daily decisions only at 23:00 UTC after availability. Official exceptional dates (2023 and 2025 delays) must be verified against the CFTC special announcements. Exclude reports first available on/after 2026-01-01. Fail closed if eligible releases are not strictly increasing or if any 2026 data enters training. Output immutable ledger, its SHA-256, coverage, excluded rows, and decision `PASS_CAUSAL_DATA_ONLY` only when all source gates pass.

Expected frozen local ledger SHA-256: `efd159d201aca666898cc5a971c33aca95215f3c518356b3b14054050d03ca36`. Prior independent local audit: 155/157 eligible; 21 special overrides; 0 accounting violations; 14–51 days lag. These figures are **not** PnL and require reproducible remote verification.

Important unresolved limitation: historical annual CFTC archives may contain later revisions; a passing availability-lag gate does not prove historical point-in-time value provenance and does not authorize final strategy promotion.

Decision contract: data-only PASS/FAIL. The subsequent Phase266 hypothesis and gates are frozen independently and cannot be rescued by post-result changes.
