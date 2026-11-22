# V98 Independent — C27 internal candidate lock (2026-11-22)

Status: **INTERNAL TRAINING CANDIDATE LOCK ONLY**. Not validated, not promoted, not paper/live. This file is not a claim of independent performance.

## Immutable candidate identity

- Repository: `DnSiii/CryptoAI-Lab`
- Authorized research branch: `research/v98-independent-zero`
- Candidate code baseline commit: `6c609dacde9f197ba58ed23546bd14fda968a035`
- C27 replay blob SHA: `e7228dc8dfa7d0819ca8085e7b067c60074b7382`
- Composed C26 model blob SHA: `5a62fc795d7a12f906726136c3bcba8fe669771f`
- C27 two-clock governor blob SHA: `632b50dae1d37285497823e49c7a518939920417`
- C27 workflow blob SHA: `d1640beab5cd4bd53bfe71ea61e1dc6a78d5dc2a`
- Training source artifact IDs: price `13444665313`; native funding `13464271018`.
- Training execution: GitHub Actions run `45056906508` (training-only).
- Eligible training symbols: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT; 1h Binance USD-M; Dec 2022 warmup to Dec 2025.
- XRP excluded. Phase083 holdout permanently ineligible.

## Selection firewall

The C27 architecture and parameter values at the baseline commit are fixed for its **first** independent prospective validation. No sign, horizon, threshold, gross, leverage, governor, router, or cost tuning is allowed on the independent sample. Any subsequent change creates a **new** candidate with its own prospective sample and cannot inherit C27 validation. All 2023–2025 diagnostics and the Governor-off counterfactual are **training observations**, never independent validation.

## Independent validation contract (not executed)

1. Before reading any future data, separately record a complete source provenance receipt (exchange, product, asset universe, UTC timestamps, raw file SHA-256, native funding event SHA-256, acquisition time, gaps, corrections and coverage). Do not substitute another exchange, backfill missing events, or reintroduce XRP.
2. Validation must be **strictly later than 2025-12-31 UTC**, with no overlap with training, and must not use the contaminated Phase083 holdout. This prospective period is validation-only: **never feed it to model fitting or candidate selection**.
3. The existing training reader hard-stops at 2025-12 and 27048 bars. A separately namespaced validation reader and runner are required; they must carry forward the frozen C27 logic and weights, preserve historical warmup without scoring it, and forbid fitting. No validation result is available until these are built and independently reconciled.
4. Before the first validation replay, precommit the exact period, costs (1x/2x/4x/8x/12x), pass/fail gates, regime definitions, fold boundaries, missing-data policy, capital convention, exposure constraints, causal execution rules, and all audit output schemas. No post-result rescue.
5. Independently audit each hourly price/funding cashflow, next-open orders and queue, gross/net ledger, arithmetic, reproducibility, max drawdown, concentration, tails, PF, payoff, win rate, positive days, annual/period returns and compounded CAGR. A training gate PASS is not an independent PASS.
6. Only after this candidate passes precommitted independent validation may V14/V15/V99 be opened as **external benchmarks**. Never import their architecture, signals, parameters, or performance to select V98.

## Current decision

C27 is **LOCKED FOR FUTURE INDEPENDENT EVALUATION, NOT APPROVED**. Training 8x/12x economic survival passed in run 45056906508; that alone does not establish the North Star. A new independent chronological source with verifiable provenance and a validation-only runner are outstanding. Frozen/paper remain untouched.
