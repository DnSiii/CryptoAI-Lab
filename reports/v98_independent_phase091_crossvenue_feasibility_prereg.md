# V98 Independent Phase091 — Cross-venue microstructure feasibility preregistration

Status: **PREREGISTERED / DATA FEASIBILITY ONLY / NO ALPHA PNL**.

## Hypothesis class

A genuinely new information set is cross-venue price discovery: temporary, point-in-time dislocations between the canonical Binance USD-M perpetual market and an independent liquid perpetual venue may contain information not represented by single-venue OHLCV, funding, OI, taker, depth, basis or calendar families already consumed by V98.

Phase091 does **not** choose continuation versus reversal and does not compute strategy PnL. It only decides whether a reproducible historical dataset exists that could support a later separately preregistered hypothesis.

## Fixed universe and period

Symbols: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT where an economically equivalent perpetual contract exists on the second venue. Required research coverage: 2023-01-01 through 2025-12-31. Phase083 dates and all 2026 observations are forbidden for selection or feasibility scoring beyond verifying that no file accidentally crosses the training boundary.

## Required source properties

The second-venue source must be public or otherwise already authorized, machine-retrievable without private credentials, timestamped in UTC, point-in-time historical (not reconstructed from current state), and provide at minimum hourly close/mark or sufficiently granular trades/klines from which an hourly price can be deterministically built. Raw payload/file hashes and source URLs/identifiers must be recorded.

## Feasibility gates

PASS_DATA requires all of: (1) >=99.0% expected hourly timestamp coverage for at least BTC and ETH for the full 2023-2025 interval; (2) >=95.0% coverage for at least four of the five fixed symbols; (3) no look-ahead/revision field needed to construct the timestamp-t observation; (4) deterministic symbol/contract mapping and quote normalization; (5) duplicate timestamps <0.1% before deterministic deduplication; (6) no unexplained gaps >24h for BTC or ETH; (7) source can be reacquired from documented identifiers; (8) all retained timestamps <=2025-12-31 23:00 UTC.

If any mandatory gate fails, decision is **FAIL_DATA_NO_ALPHA**. No signal direction, threshold, lookback, spread transform or PnL may be tested in Phase091.

## Anti-overfit / isolation

No V99 or V16 evidence may be inspected or used. Phase083 is permanently opened and ineligible. No parameter search is allowed. A PASS_DATA result only authorizes a new Phase092 preregistration; it does not promote a candidate or open validation.
