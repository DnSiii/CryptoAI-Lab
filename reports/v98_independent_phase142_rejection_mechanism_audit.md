# V98 Independent Phase142 — rejection mechanism audit

Status: **REJECT_NO_RESCUE CONFIRMED**.

This audit is descriptive only. It does not authorize tuning, rescue, validation, or holdout access.

## Mandatory gate failure
The frozen Phase142 report fails the chronological 2024 fold twice:
- total return: -0.027301553994625194 (required > 0)
- daily Profit Factor: 0.9743855642294744 (required >= 1.02)

Aggregate training remained positive (+0.17438608792570398; PF 1.0783414921180747), and severe/supersevere stress remained positive, so the rejection is specifically chronological robustness rather than aggregate collapse.

## Failure mechanism diagnostics
- 2024 payoff is 0.8858050583904313, consistent with loss magnitude overwhelming winners despite a nonzero hit rate.
- Sideways regime return-sum approximation is -0.205771321874902, versus positive bear and bull approximations. This is descriptive evidence of regime fragility, not permission for a regime filter.
- Top-10 positive-day contribution share is 0.14079925684525232, well below the frozen 0.35 limit; failure is not explained by a handful of best days.
- Largest positive raw-price contribution share is SOLUSDT at 0.44010796029598975, below but close to the frozen 0.45 cap. No basket change is authorized.
- Aggregate max drawdown is -0.19242408103911646, inside the -0.35 floor.
- Severe: return +0.13078250702908623, PF 1.0635109540227194.
- Supersevere: return +0.06277123857483402, PF 1.0396855753420573.

## Reproducibility / causality
The persisted report states ALFRED PIT reacquisition hash verification passed and records immutable PIT, activation, targets, and preregistration SHA-256 digests. The economic-use lag remains d+2 and Phase141 result use is false.

## Decision
Phase142 remains **REJECT_NO_RESCUE**. No sign flip, lookback/threshold change, basket change, gross change, timing change, cost change, or post-hoc regime filter is admissible.

Phase143 is scientifically distinct and remains DATA_ONLY until its separately frozen integrity gate is executed and persisted.
