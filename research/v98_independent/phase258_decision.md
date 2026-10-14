# V98 Independent Phase258 — Bitcoin Network Hashrate DATA_ONLY decision

Status: **PASS_DATA_ONLY**.

The fixed Blockchain.com hashrate endpoint passed every preregistered data gate before any crypto-price join or PnL.

Training coverage:
- expected UTC days: 1,096
- observed: 1,093
- coverage: 99.73%
- first date: 2023-01-01
- last date: 2025-12-31
- max gap: 3 days
- invalid source points: 0
- all values finite and positive
- deterministic normalized CSV SHA-256: 1586810e6c1a98b3f17a0f3c348c167834ca9f9b2ab8d58cea9e2d07b29725fb
- raw response SHA-256: 7a07d1bb389bc6c846a7215caacc547ef47694aa58605d034d8d4456e56bd283

No alpha direction, threshold selection, parameter search, price/return join, backtest, validation or holdout access occurred.

PASS_DATA_ONLY authorizes only a separately preregistered economic hypothesis using completed prior-day hashrate. It does not promote a strategy or open validation/holdout.
