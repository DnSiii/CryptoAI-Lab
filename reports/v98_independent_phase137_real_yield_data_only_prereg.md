# V98 Independent Phase137 — US 10Y Real Yield DATA_ONLY preregistration

Status: **FROZEN BEFORE DATA VALUES / RETURNS / ALPHA / PNL**.

## Hypothesis family

A distinct macro discount-rate family: the U.S. 10-year Treasury inflation-indexed constant-maturity real yield (FRED `DFII10`) may provide an orthogonal, economically grounded state variable for crypto risk appetite. Phase137 is strictly a data feasibility/integrity gate. It does **not** test direction, threshold, correlation, return, alpha, portfolio weights, or PnL.

This family is distinct from prior V98 DXY, global-liquidity, RRP, credit-stress, policy-uncertainty, financial-stress, sentiment, on-chain, funding, price-volatility, and jump-breadth studies. No V99/V16 evidence is consulted.

## Frozen data contract

- Source: FRED public CSV.
- Series: `DFII10`.
- Training window only: 2023-01-01 through 2025-12-31 inclusive.
- Parse ISO `observation_date`; retain only finite DFII10 observations inside the training window.
- No fill, interpolation, forward-fill, imputation, normalization, winsorization, or transformations.
- Output may expose only counts, coverage/integrity flags, deterministic hashes, and decision. **Actual yield values and descriptive statistics are forbidden.**
- Validation and final holdout must remain inaccessible/unopened.

## Frozen gate

PASS_DATA_ONLY iff: HTTP 200; weekday coverage >=95%; zero malformed dates; zero duplicate finite dates; zero finite observations outside the training window; deterministic canonical hash on repeated execution. Otherwise `REJECT_DATA_SOURCE_NO_RESCUE`.

A PASS does not authorize PnL. It only permits a separately preregistered Phase138 economic hypothesis before any DFII10 value, correlation, return, alpha, or PnL is inspected. A FAIL closes this source/family without schema/threshold rescue.

## Anti-overfit / isolation

No parameter search. No use of Phase083 holdout. No validation access. No V16 or V99 use. No tuning from Phase136's 2025 failure. Phase137 cannot be used as a post-hoc filter for Phase136.
