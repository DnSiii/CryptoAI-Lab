# CryptoAI V13 — forward paper protocol

## Frozen candidate

- Candidate: `CryptoAI V13 PIT Carry-Core + Circuit Breaker`
- Historical configuration: `config/candidate_v13_circuit_breaker.json`
- Historical validation: `reports/candidate_v13_circuit_breaker_validation.json`
- Real exchange orders: absent and prohibited

## Start rule

The first execution of `scripts/paper_once_v13.py` freezes the later of the
model-initialization hour and the last available market timestamp. Once stored,
that boundary never follows later downloads. Performance is counted only on
timestamps strictly newer than the frozen boundary. Backfilled history from
before the model freeze cannot be presented as forward paper performance.

The current durable boundary is `2026-08-13T19:00:00+00:00`. GitHub Actions
runs at minute 17 of every hour and checks the official, checksummed Binance
USD-M daily archives. New observations enter the paper ledger when Binance
publishes the corresponding daily file; a cycle is refused if BTC or ETH moves
beyond the 48-hour publication window. Compact state, data-sync evidence, and
the latest snapshot are written to the `paper-results` branch. No exchange
credential is required or accepted by this workflow.

## Minimum evidence before any capital discussion

1. At least 90 calendar days and 60 days containing a non-zero position.
2. At least 100 position decisions after the frozen boundary.
3. No implementation drift between the frozen candidate and the paper runner.
4. Costs, funding, delay and circuit-breaker state recorded on every run.
5. No liquidation or guard failure.
6. Positive net forward return and no unresolved data gap.
7. A new review of concentration in BTC, ETH and the funding sleeve.

Passing this protocol permits a later capital-risk discussion; it does not
automatically authorize real money.
