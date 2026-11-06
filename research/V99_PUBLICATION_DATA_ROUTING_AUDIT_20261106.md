# V99 publication data routing audit — 2026-11-06 18:43 UTC

Scope: read-only inspection of gh-pages JavaScript and two branch sync manifests. No trading orders, paper rewriting, or holdout access.

## Verified routes
- gh-pages/dashboard/app_v2.js: REMOTE_DATA points to raw.githubusercontent.com/DnSiii/CryptoAI-Lab/paper-results/dashboard/dashboard_data.json; on failure it falls back to relative dashboard_data.json.
- gh-pages/dashboard/paper_classic.js: PC_LEDGER_BASE points to paper-results/reports/ and requests paper_<key>_ledger.json.
- gh-pages/dashboard/v99_research.js: DATA_URL points to paper-results/dashboard/dashboard_data.json, but load loop attempts local dashboard_data.json FIRST, then remote. This creates a stale-first risk if the local copy is old, even while paper-results is fresh.
- gh-pages/reports/paper_data_sync_v13.json: generated_at_utc 2026-08-14T04:41:39.918929+00:00; target_latest_closed_hour 2026-08-14T03:00:00+00:00.
- paper-results/reports/paper_data_sync_v13.json: generated_at_utc 2026-11-06T18:37:04.290132+00:00; target_latest_closed_hour 2026-11-06T17:00:00+00:00.
- GitHub Actions 42272132850 (paper) and 42272087775 (dashboard) completed success. Success is not independent proof of browser-served data.

## Immediate safe fix to evaluate
Change ONLY v99_research.js data fetch priority to remote paper-results first, with local fallback permitted only after explicit freshness comparison against the remote or a reliable timestamp, and visibly mark fallback/stale. Better: fetch both, validate schema and market timestamps, choose freshest trustworthy snapshot, display source/time, fail closed if neither is trustworthy. Add adversarial tests for stale local vs fresh remote, remote unavailable, missing timestamps, malformed JSON, and time regression. Do not alter paper-results, frozen branches, historical ledgers, V13 verifier, or trades. Verify via Actions and real Pages browser response before claiming resolved.

## Research disposition
NO PROMOTION. D1 and C1 rejected; I1 requires original full Deribit option history and written licensing/authorization. No new economics run in this audit.
