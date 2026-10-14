# V99 R106 — prospective OKX native contract and funding receipts

This independent folder records append-only, first-hand as-of public **OKX USDT perpetual contract specifications** (contract size, currency, tick, lot, minimum size) and **funding-rate notices** with raw response hashes and UTC server timing.

**Do not equate these funding-rate notices with actual funding settlement.** They have no independently authenticated PnL cashflow, fee tier, fill slippage, execution, or margin evidence. The user cannot claim profitable paper trading from these receipts. Native OKX contract semantics differ from Binance (e.g. contract multiplier), so frozen Binance R106 engines must not be transplanted without separate research and cost validation.

Each new observation is written into its UTC acquisition-hour folder only if absent. Existing folders are immutable. The workflow rejects hash mismatches and out-of-order timestamps; no authorized operation modifies `paper-results`, Frozen, Train, validation or untouched final holdout.

Files: original 10 first-party metadata/funding JSON responses for exactly five preregistered OKX swaps, first-party before/after clock responses, `manifest.json`, `receipt_commit_provenance.json`.

Retention: immutable Git commits in this receipt branch plus optional GitHub Actions ZIP artifacts (90 days). No exchange/API trading credentials are used.
