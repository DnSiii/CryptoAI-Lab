# V98 Independent — Phase064 decision

Status: **REJECT_NO_RESCUE**

Phase064 was evaluated exactly as preregistered on the frozen chronological training folds 2023, 2024 and 2025. The training gate failed, therefore validation remains closed and the final holdout remains untouched.

## Frozen training evidence

- Aggregate return: +90.8127%
- Aggregate daily Profit Factor: 1.1323
- Aggregate max drawdown: -38.4751% (gate required > -35%)
- 2023: +78.6894%, PF 1.3457, max DD -23.7055%
- 2024: +45.9413%, PF 1.1955, max DD -29.5836%
- 2025: -27.6631%, PF 0.8848, max DD -38.4751%
- Severe costs: +69.0730%, PF 1.1125, max DD -40.4882%
- Supersevere costs: +38.1615%, PF 1.0801, max DD -43.6290%

Formal gate failures recorded by the executable evidence:
1. `max_drawdown<=-35%`
2. `2025_return<=0`
3. `2025_pf<=1.02`

## Decision

The family is rejected without rescue. No inversion, threshold/lookback/gross adjustment, asset removal, regime filter, source substitution, or other post-result parameter search is permitted for Phase064. Its strong 2023/2024 and aggregate return do not override the preregistered chronological-fold and drawdown failures.

Validation: **NOT OPENED**.
Final holdout: **UNTOUCHED**.
V99/V16 used for selection or tuning: **NO**.
