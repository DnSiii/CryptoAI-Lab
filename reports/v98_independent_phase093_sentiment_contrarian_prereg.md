# V98 Independent Phase093 — Lagged extreme-sentiment contrarian preregistration

Status: **PREREGISTERED / TRAINING ONLY / PARAMETERS FROZEN BEFORE PNL**.

Phase092 passed data feasibility with 1095/1096 training days (99.91%), zero duplicates, max one-day missing gap, valid 0..100 values and a hashed/reacquirable frozen source. Phase093 is the single authorized alpha test for this information class.

## Frozen causal signal

At UTC day t, use only the most recently published Fear & Greed `value` whose source timestamp is strictly before day t. If lagged value <=25, hold an equal-weight LONG basket of BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT for day t. If lagged value >=75, hold the same basket SHORT. Otherwise hold cash. Missing sentiment is forward-filled for at most 3 calendar days; beyond that exposure is zero. No classification text is used.

## Frozen exposure and execution

Gross exposure when active: 0.75, equally divided across the five symbols; no leverage scaling, volatility targeting, regime filter, symbol selection, threshold search, stop, take-profit, rescue, or parameter sweep. Position changes occur at the first canonical daily boundary after the lagged sentiment observation is known. Funding is charged using the canonical point-in-time funding data. Turnover costs are charged on every absolute weight change.

Cost scenarios are frozen to the existing V98 Independent BASE / severe / supersevere conventions already used by the canonical evaluator; no cost may be relaxed after results.

## Training and gates

Selection interval is training-only through 2025-12-31 with chronological 2023, 2024 and 2025 folds. Validation remains closed. Phase083 and every 2026 observation are forbidden.

PASS_TRAINING requires all of: aggregate net return >0; PF >1.10; max drawdown >=-35%; every chronological fold net return >0; severe return >0 and PF >1.0; supersevere return >0 and PF >1.0; no single asset contributes >60% of absolute aggregate contribution; and no pathological tail/concentration condition identified by the standard V98 diagnostics. Report CAGR, max drawdown, PF, payoff, win rate, positive days, folds, regimes, concentration/tails, turnover, funding, costs and reproducibility hashes.

Any failed mandatory gate => **REJECT_NO_RESCUE**. PASS_TRAINING only authorizes a separately frozen validation phase. It does not authorize final holdout.

## Isolation

No V99/V16 evidence. No Phase083 selection use. No 2026 tuning. No alternate sentiment source, threshold, direction, lag, basket, gross, regime, cadence or cost rescue after PnL is observed.
