# V99 R106 — Immutable prospective OKX receipts

This directory is an **append-only historical evidence store**. It is **not** the published V99 paper ledger and is never an input to an economic TRAIN optimization on the 2026 forward period.

A receipt is first seen only at its recorded UTC HTTP request/receive times. The original raw HTTP JSON, a manifest with SHA-256, OKX server-clock responses and closed 1H candles are stored under a unique UTC acquisition-hour folder. Repeating an already present hour must fail closed: no replacement, correction, or force-push.

## Restrictions

- Collect **only** the five Phase136 frozen OKX USDT swaps: BTC, ETH, SOL, XRP and DOGE; do not conflate OKX native swap economics with Binance F1/F3/F7 economics.
- Complete hourly bar is accepted only after the OKX API returns `confirm=1` and the UTC bar close is no later than observed acquisition time.
- If a query is blocked, stale, or malformed, record the failed GitHub run, **not** a fabricated receipt.
- Each success is first-party HTTPS plus OKX server clock and SHA-256 byte evidence. It is not independent venue-signed proof, not retroactive symbol first-seen history, and does not authorize paper trades or R106 promotion.
- Minimum admissible decision is the receipt's acquisition hour **plus two UTC hourly boundaries**. The supplied `first_seen` clock may not be backdated.
- **Never** overwrite old `paper-results`, old V99/R106 Frozen, or the final holdout; this receipt branch remains separate.
- Every evidence commit must be a normal Git fast-forward append with signed GitHub Actions identity. Immutable file path after initial creation.
- Source artifacts in GitHub Actions may expire. The canonical evidence is the bytes in this receipt branch and their Git history.
- Chronological source receipts are required **in addition** to native OKX funding, fees, funding times, execution slippage, exchange contract specifications, and complete PnL accounting before new paper can be promoted.

**Initial branch:** created 2026-10-14, with no source backfill. Earliest actual evidence is whichever clean acquisition the first live receipt workflow independently confirms.
