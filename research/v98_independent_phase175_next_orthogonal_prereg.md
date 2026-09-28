# V98 Independent Phase175 — orthogonal data-family discovery preregistration

Status: preregistered after Phase172/173 rejection and before any new economic result inspection.

## Isolation

- Branch: `research/v98-independent-zero` only.
- V98 Independent namespace only.
- V16 Frozen, V99 Frozen, all V99 branches/workflows/reports/paper state are forbidden inputs.
- Phase172 validation is terminally rejected; no rescue or transformation of its T10Y2Y signal is permitted.
- Final holdout remains unopened and must not be queried during discovery/training/validation.

## Scientific objective

Inspect a genuinely orthogonal **US dollar broad-strength macro data family** (official/public source preferred) as a DATA_ONLY candidate. This phase is identity/integrity/causality discovery only; it must not compute crypto PnL, correlations to future crypto returns, thresholds, directions, or choose variants using economic performance.

Candidate family concept: a broad trade-weighted US dollar index or equivalent official broad-dollar series. The exact series may be accepted only if source identity, semantics, historical coverage, and publication timing/causal availability can be documented without proxy ambiguity.

## DATA_ONLY gates

PASS_DATA_ONLY requires all of:

1. authoritative series identity and units are unambiguous;
2. deterministic reacquisition or immutable evidence hash is possible;
3. adequate coverage for the frozen training era 2023-01-01 through 2025-12-31;
4. missing/duplicate/non-finite observations are quantified; no hidden imputation/backfill;
5. publication/availability semantics support a conservative causal lag fixed before economic testing;
6. no final-holdout observations are needed to establish any gate above.

If identity or causal timing is ambiguous, reject the family rather than substitute a convenient proxy.

## If DATA_ONLY passes

A later phase may preregister exactly one economically directional hypothesis before inspecting its crypto PnL. Direction, lag, lookback, threshold, basket, gross target/cap, cost model, folds and gates must be frozen in that later preregistration. No grid search/rescue is permitted.
