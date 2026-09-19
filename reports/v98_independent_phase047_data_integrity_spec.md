# V98 Independent Phase047 — External Metrics Data-Integrity Specification

This specification is frozen before Phase047 return evaluation. It governs only V98 Independent open-interest data acquisition and prevents data repairs from becoming hidden alpha tuning.

## Source and timestamp rules

Use Binance public USD-M **daily** metrics archives only. The earlier monthly-path assumption was an acquisition-path error: the preregistered feasibility probe subsequently verified the daily archive across all sampled symbols/years. This correction changes source transport only and does not change the Phase047 economic hypothesis, sign, lookback, rebalance cadence, neutralization, gross, universe, or evaluation gates.

Preserve each archive timestamp as UTC and require monotonic, duplicate-free observations per symbol. A portfolio decision at hour `t` may use only a metrics record whose source timestamp is strictly earlier than `t`; no backfill from a later observation is allowed. The alpha formula itself additionally uses the preregistered `t-1` versus `t-25` 24h OI change.

## Required field

`sum_open_interest` must parse as finite and strictly positive. Schema aliases are permitted only if the probe proves that Binance changed a header while the economic field is demonstrably identical; any alias mapping must be documented before backtesting. Long/short ratios, taker ratios and other metrics fields are ignored for Phase047 and cannot be substituted if OI is absent.

## Coverage and missingness

The source-feasibility gate requires stable schema across sampled dates in 2023, 2024, 2025 and 2026 for every current V98 symbol. Full acquisition must then report first/last timestamp, row count, duplicate count, nonpositive/invalid OI count, missing expected timestamps and SHA-256 per source archive. Symbols/hours with unavailable OI are ineligible at that decision; values are not interpolated across missing source intervals.

## Point-in-time universe

The existing candle-derived V98 liquidity membership remains authoritative and causal. External metrics cannot be used to decide which contracts enter the top-10 universe. OI only scores names already eligible under that membership. This prevents a new survivorship/liquidity-selection channel.

## Alignment and reproducibility

Canonical Phase047 metrics must be stored only in V98-namespaced paths/artifacts and generated deterministically from source archives. Re-running acquisition against identical archive bytes must produce identical canonical OI values and manifest hashes. Acquisition code must not read V99 files/state/reports.

## Failure policy

Any ambiguous timestamp, unstable required-field semantics, material unexplained gaps, or insufficient historical coverage blocks the Phase047 backtest. Allowed remediation is limited to source acquisition/parsing/alignment. The preregistered signal sign, 24h window, 24h rebalance, 720h beta neutralization and 0.75 gross may not change in response to data characteristics or later performance.

Validation and final holdout remain closed during all acquisition/integrity work.
