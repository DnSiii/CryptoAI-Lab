# V98 Independent — Phase224 pre-execution independence + data audit

Status: **BLOCK_EXECUTION_UNTIL_REALIZED_FUNDING_SOURCE_EXISTS**
Scope: branch `research/v98-independent-zero`, V98 namespace only.

## 1. Hypothesis identity / historical independence
Phase224 preregisters **realized funding dislocation convergence**: enter contrarian to an extreme *realized* funding print, with BTC realized funding as the market-control condition. This is economically distinct from the recent OHLC/residual-return families (Phase221 cross-sectional residual momentum, Phase222 range-breakout design, Phase223 idiosyncratic volatility-shock mean reversion). It is also distinct from Phase206's *forecast-only* funding design **provided that Phase224 consumes genuine realized funding prints and does not substitute forecast/premium-index observations**.

Therefore the family is conditionally independent: independence is preserved only if the input semantic is realized funding.

## 2. Data provenance audit
The only funding dataset currently visible inside the V98 namespace is `research/v98_independent/data/phase206_funding/`, whose own integrity audit identifies:
- source: Binance public `fapi/v1/premiumIndexKlines`;
- transport: GitHub Actions;
- semantic: **forecast_only**;
- `realized_funding_source_present: false`;
- `phase206_execution_allowed: false`.

The Phase206 transport amendment likewise states that premium-index history is not a substitute for historical realized funding and explicitly prohibits silent substitution.

Phase224 preregistration requires a causal `realized_funding(t-1)` trigger and BTC realized funding control. Consequently the currently namespaced forecast-only dataset cannot satisfy Phase224 without changing the frozen scientific question.

## 3. Anti-overfit / causality disposition
Do **not** execute Phase224 against premium-index / forecast funding. Doing so would convert a preregistered realized-funding hypothesis into a different ex-ante premium hypothesis after registration and would contaminate interpretation.

Do **not** open 2026+ while sourcing the data. The required source must permit a training-only snapshot ending 2025-12-31 with timestamps sufficient to prove that each realized funding observation was known before the next-bar entry.

Required provenance fields before execution:
1. venue + endpoint/dataset identity;
2. exact realized funding timestamp semantics;
3. asset universe BTC/ETH/BNB/SOL/XRP;
4. earliest/latest timestamps and row counts per asset;
5. duplicate/missing timestamp audit;
6. deterministic content hashes;
7. explicit max timestamp `< 2026-01-01T00:00:00Z`;
8. evidence that values are realized settlements, not predicted next funding or premium-index proxy.

## 4. Cost/funding accounting invariant
Phase224 uses funding itself as the signal. If the eventual evaluator also charges funding cashflows to PnL, signal and cashflow must come from the same realized series with a causal settlement convention. No forward funding value may be used to select a trade that receives that same not-yet-known settlement.

Trading costs remain frozen at 7/14/28 bp round-trip for base/severe/supersevere. Chronological folds remain 2023/2024/2025; 2026+ remains unopened.

## 5. Decision
**BLOCK_EXECUTION_UNTIL_REALIZED_FUNDING_SOURCE_EXISTS.**

This is a data-integrity block, not a failed alpha result and not permission to rescue/tune the hypothesis. Once a genuine realized-funding training-only snapshot is present inside the V98 namespace and passes the provenance invariants above, Phase224 may proceed exactly as preregistered. Champion remains unchanged meanwhile.
