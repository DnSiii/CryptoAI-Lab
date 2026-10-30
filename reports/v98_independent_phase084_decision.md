# V98 Independent Phase084 — Decision

Decision: **REJECT_NO_RESCUE**.

The frozen training run completed successfully, but the preregistered gate failed. Aggregate BASE was +19.88%, PF 1.0956 and max drawdown -23.33%; however 2025 was -9.46% with PF 0.8310. Severe was -15.24% and supersevere -51.20%. The explicit failures are `2025_return<=0`, `2025_pf<=1.00`, `severe_return<=0`, and `supersevere_return<=0`.

No validation is opened. No sign flip, streak-length change, gross/cadence/symbol/regime/cost rescue or reinterpretation is allowed. Phase083 results were not used to tune Phase084 and must not be used to tune future candidates. A future final candidate requires a genuinely new future untouched holdout.
