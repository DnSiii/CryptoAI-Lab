# V98 Independent — Phase178 preregistration

Status: PREREGISTERED / DATA_ONLY

## Scientific question

Can an orthogonal US credit-risk/stress series be acquired with sufficient identity, coverage, causal publication timing and deterministic reproducibility to justify a later economic hypothesis, without using any crypto PnL, validation, final holdout, V16 or V99 information?

## Fixed data family

Primary series: ICE BofA US High Yield Index Option-Adjusted Spread (`BAMLH0A0HYM2`) from FRED.

Rationale: credit-risk stress is economically distinct from Phase175/176 broad USD strength. It can plausibly proxy global risk appetite / financing stress without retuning the rejected DTWEXBGS hypothesis.

## DATA_ONLY protocol

Window fixed before acquisition analysis: 2023-01-01 through 2025-12-31 only.

Required checks before any economic/PnL use:

1. Confirm exact series identity and source metadata.
2. Record raw schema and observation count by calendar year.
3. Require chronological monotonicity, no duplicate dates, finite positive observations after explicit missing-value handling.
4. Report missing observations and maximum calendar gap; do not silently interpolate future information.
5. Determine a conservative causal availability rule from source publication semantics. Same-day use is forbidden unless independently proven safe; otherwise use next-US-business-day availability or more conservative.
6. Acquire twice independently and require deterministic normalized-data equality / SHA-256 identity.
7. Do not inspect crypto returns, strategy PnL, validation, or final holdout during DATA_ONLY.
8. Do not use V16 or V99 results for selection, transformation, thresholds, or timing.

## Anti-overfit locks

No threshold search, lookback search, parameter sweep, economic correlation ranking, candidate comparison, or rescue is permitted in Phase178. Passing DATA_ONLY only authorizes a separately preregistered economic hypothesis. Failure closes the phase or requires infrastructure repair only when the failure is demonstrably operational rather than scientific.

## Holdout state

Validation: CLOSED.
Final holdout: CLOSED / UNTOUCHED.
V16 used: NO.
V99 used: NO.
