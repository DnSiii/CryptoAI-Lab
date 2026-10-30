# V98 Independent Phase072 — training decision

Status: **REJECT_NO_RESCUE**.

Frozen hypothesis: 30-day cross-sectional volatility-normalized momentum.

Observed training evidence from the frozen Phase072 run:
- aggregate return: +8.6163%
- daily Profit Factor: 1.04439 (gate > 1.05 failed)
- max drawdown: -37.4498% (gate >= -35% failed)
- 2023: -10.6532%, PF 0.96310 (both chronological fold gates failed)
- 2024: +18.9636%, PF 1.14006
- 2025: +2.2118%, PF 1.03614
- severe: -10.9546% (failed)
- supersevere: -34.4161% (failed)

No parameter rescue, retuning, validation opening, or holdout inspection is permitted for Phase072. Validation remains unopened. Final holdout remains UNTOUCHED. V16/V99 were not used for selection or tuning.

Decision rationale: multiple independent training gates failed simultaneously, including chronological stability, drawdown, PF and transaction-cost stress robustness. The candidate is therefore rejected rather than modified after seeing its PnL.
