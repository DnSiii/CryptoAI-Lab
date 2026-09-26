# V98 Independent — Phase145 VIX DATA_ONLY preregistration

Status: **PREREGISTERED — DATA_ONLY**.

## Scientific rationale

Phase144 SP500 risk-on is closed `REJECT_NO_RESCUE`; no SP500 parameter, threshold, lag, sizing, direction, or combination may be tuned. Phase145 starts a scientifically distinct external-data family: option-implied equity volatility (CBOE VIX via FRED `VIXCLS`). This is a volatility/risk-aversion state variable rather than equity-price trend.

## Frozen scope

- Series: FRED `VIXCLS` only.
- Calendar: 2023-01-01 through 2025-12-31, training era only.
- This phase is **DATA_ONLY**. It may inspect only dates, finite numeric parseability, missingness, coverage, ordering, uniqueness, schema identity, and reproducibility hashes.
- Required coverage: >=95% globally and independently in 2023, 2024, and 2025 versus weekdays.
- Two independent acquisitions must produce identical canonical SHA-256 over `date,normalized_value` and identical integrity metadata.
- No imputation.

## Economic firewall

Phase145 must not compute or expose VIX levels, changes, returns, thresholds, quantiles, correlations, crypto outcomes, positions, PnL, Profit Factor, payoff, win rate, positive days, drawdown, regime attribution, concentration, tails, or candidate rankings.

No economic Phase146 is authorized unless Phase145 is persisted as `PASS_DATA_ONLY`. If data quality fails, reject the data phase without rescue. If Phase145 passes, any economic hypothesis must be separately preregistered before inspecting relationships between VIX and crypto outcomes.

Validation and final holdout remain unopened. V16 and V99 are forbidden as inputs, benchmarks, selectors, or tuning references.
