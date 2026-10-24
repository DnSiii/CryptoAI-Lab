# V99 — preregistered weekly PIT options information coverage gate (2026-10-24 BRT)

**DATA_ONLY/HOLD — NO PROMOTION.** This note fixes the coverage criteria before reading the new weekly source results. Source feasibility is not a trading edge, and a passing GitHub workflow is not economic validation.

## Exact immutable scope and rationale

- Existing R106 TRAIN only: 2021-12-09 00:00 UTC through 2023-10-01 00:00 UTC exclusive. Original five chronological fold edges are imported from the source-gated D1 module. No validation [2023-10-01, 2024-01-18) or holdout >=2024-01-18 is queried.
- One fixed decision clock: Monday 00:00 UTC. Per BTC and ETH, request first-party Deribit historical option **trades** in [decision-24h, decision), sorted newest first, bounded at 100 trade records per decision. Raw exchange bytes and SHA-256 hashes are archived; API errors are explicit, never imputed as positive coverage.
- Information eligibility, not a strategy: each currency/decision must have >=2 distinct option strikes with IV in **each** of short (7–45 days to expiry) and long (46–120 days) maturity bands, separately for calls and puts. Trades must be no more than six hours old and strictly earlier than the decision. Historical instrument expiry is parsed from the original exchange symbol. No option prices are scored.
- A fold meets the information coverage threshold only if **both BTC and ETH** have >=70% eligible weekly decisions. At least 4/5 folds are required to warrant designing a single complete integrated engine. Thresholds are fixed ex ante, not optimized on observed results.
- The 100 most recent trades constitute a deliberately bounded **lower-bound sample**, not full options-chain coverage. A negative outcome only rejects this precise sampled information contract; it does not disprove the wider options family. A positive outcome does not establish tradable 25-delta skew, stable IV surfaces, executable quotes, alpha, or historical profits.
- Independent CI oracle reopens raw receipts, verifies SHA-256, checks strict timestamps and five folds, reconstructs strike/side/maturity eligibility without importing the collector classifier, and independently checks the aggregate coverage decision.
- The workflow is read-only and has no order credentials, no account mutations, no economic train, no promotion. V16 Frozen, V99 Frozen, legacy champion, paper/results and all quarantined data are untouched.

## Actual next gate (not implied by this test)

If sufficient: preregister **one distinct** causal economic mechanism using PIT options information to condition spot/perp decisions; then obtain original venue prices, cost/fee provenance and conservative fills; execute complete severe/supersevere 5-fold TRAIN accounting, 3x2 regimes, risk/tail/DD, benchmark envelope and independent cash replay before freezing. Only after a genuinely successful TRAIN freeze may sealed validation open. If insufficient: stop this particular bounded data contract and document precisely whether missing source, stale trades, or sparse option-chain coverage caused failure. No serial posthoc strategy search.

**No ROI. No model promotion. No orders. No paper publication.**
