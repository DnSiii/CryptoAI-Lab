# V99 R106 — 2026-10-16 03:42 BRT: atomicity evidence separation

Scope: `research/v99-r106-native-all-regime-engine`. Only research audit, tests, source-only CI and this note changed; V16 Frozen, V99 Frozen, holdout, models, economic trials and champions remain untouched.

The chain now distinguishes independently verified market continuity from same-run **claims** in the two first-party manifests. Adjacent candidate links and longest same-run-claimed streak are reported separately. Matching run IDs are not GitHub attestations or exchange signatures. Even two consecutive candidate hours cannot authorize PnL or promotion.

Latest independently observed durable head `2258482917bc0800e9cdde6459a0a572edd5a701` (2026-10-16 06:21 UTC): 8 paired UTC buckets out of 35 (2026-10-14T20 through 2026-10-16T06), 27 missing, zero adjacent. Official audit run 38850522878 verified 22 source run/artifact metadata records at 04:25 UTC, when the chain covered 8/33. A later terms-only capture at 06 UTC did not create an atomic pair.

Original-byte market capture from 01 to 04 UTC advanced 3 confirmed candle hours (not consecutive source acquisition). Public funding notices 00 to 04 UTC were still pre-settlement forecasts; the settlement-specific audit correctly rejected them. Native fees and position-specific funding cashflows remain unauthenticated.

Decision: R106 DATA_ONLY/HOLD, no validated new champion or R106 ROI. Next: gather genuinely consecutive immutable atomic pairs, independently attest each run and original byte, then separately authenticate actual native costs and settled position funding. Never backfill missing hours.
