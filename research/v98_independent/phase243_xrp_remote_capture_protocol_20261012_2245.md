# V98 Independent Phase243 — source-only remote daily capture protocol (2026-10-12 22:45 BRT)

Branch research/v98-independent-zero; namespace research/v98_independent and .github/workflows/v98-independent-* only. This is a continuation of the already frozen 2026-10-10 12:48 daily/minute source preregistration, not a new alpha hypothesis.

## Frozen data and controls
- Only XRPUSDT Binance USD-M perpetual 2023-11 monthly 1h, 2023-11-14 daily 1h and daily 1m, each with its own .CHECKSUM; no 2026+ / holdout, no V99 or V16.
- Preserve raw ZIP and sidecar bytes as immutable workflow artifacts, never repair or overwrite originals. Verify ZIP SHA256, one expected CSV member, exact row counts 720/24/1440, strict chronological UTC open/close boundaries, full OHLC and volume schema.
- Compute physical quote-volume intervals [base*low, base*high] for total, buyer and seller residual independently at all 1m/1h bars. Compare the suspicious 2023-11-14 11:00 UTC monthly 1h bar with daily 1h and aggregate of the 60 1m bars. Compare all 24 hourly OHLC, total/base quote, taker buy base/quote and trade count; record mismatches, including other hours.
- Frozen conservative tolerances for 1m additive rollup: max(1e-6, 1e-9 * abs(sum)) base units; max(1e-4, 1e-9 * abs(sum)) quote units. Exact integer trades, OHLC and 1h-to-1h numerical fields. These tolerances are data serialization allowances, never fit to outcomes.
- Print deterministic JSON summary, source hashes, source-field witnesses, physical failures and status to job logs; upload raw evidence artifacts even if cross-resolution reconciliation fails. No source consistency result from a single provider establishes fully independent provenance.

## Decision firewall
- Missing/unavailable source => INCOMPLETE_SOURCE; any contradiction or physical failure => QUARANTINED_CONTRADICTION; all same-provider checks pass => CONSISTENT_UNAUTHENTICATED. All three prohibit strategy execution, holdout access and champion promotion until full frozen 2022-12–2025-12 source grid and native funding are authenticated.
- Phase240 remains REJECT; Phase243 remains BLOCKED_SOURCE; champion NONE. Preserve chronological folds, base/severe/supersevere fees and funding, regimes, tails, concentration, max drawdown, PF, payoff, win rate, positive days and reproducibility for any future eligible experiment.
