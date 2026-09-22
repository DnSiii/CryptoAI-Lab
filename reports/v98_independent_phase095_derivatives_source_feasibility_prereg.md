# V98 Independent Phase095 — independent derivatives source feasibility preregistration

Status: **PREREGISTERED / DATA ONLY / NO ALPHA / NO PNL**

## Purpose

Test whether a genuinely independent historical derivatives-positioning source can support later V98 Independent research without reusing the already-consumed Binance positioning/open-interest family or the failed Phase091 Bybit endpoint.

This phase MUST NOT compute returns, choose a directional trading rule, inspect validation/final holdout, or use any 2026 observation for selection.

## Independence constraint

Phase047 already consumed Binance public USD-M metrics (`sum_open_interest`, trader ratios and taker ratio) as an alpha family. Therefore Binance USD-M metrics are **ineligible** as the Phase095 source even though their historical point-in-time coverage was previously demonstrated. Phase091 already attempted Bybit and received HTTP 403; Phase095 MUST NOT silently retry or substitute that endpoint after observing data.

A source is admissible only if all of the following are true before any alpha specification:

1. Source/provider is independent of Binance USD-M metrics and of the Phase091 Bybit endpoint.
2. Historical observations cover at least 2023-01-01 through 2025-12-31 for BTC and ETH; broader V98 universe coverage is desirable but not required for this feasibility gate.
3. Observations carry exchange/provider timestamps or immutable period timestamps sufficient for strict causal alignment.
4. No forward-fill across publication periods and no interpolation across missing periods.
5. Raw payload/archive provenance can be recorded with URL/source identifier and SHA-256 (or equivalent immutable provider checksum).
6. Duplicate timestamps, invalid timestamps, missing-period fraction, first/last observation and cadence are explicitly audited.
7. Data can be acquired reproducibly from the GitHub Actions environment without credentials committed to the repository.

## Frozen feasibility gates

`PASS_DATA_ONLY` requires, for both BTC and ETH:

- coverage begins no later than 2023-01-07 and ends no earlier than 2025-12-24;
- >= 95% expected-period coverage over 2023-2025 at the source's native cadence after deduplication;
- zero invalid timestamps after deterministic parsing;
- zero duplicate timestamps after deterministic stable deduplication;
- strictly monotonic canonical timestamps;
- no observation assigned earlier than its provider/exchange timestamp;
- provenance/checksum recorded;
- acquisition is reproducible without inspecting any price return, V98 candidate PnL, validation, Phase083, or future holdout.

Any mandatory failure => `FAIL_DATA_NO_ALPHA`. No source-shopping is allowed after seeing any alpha because Phase095 contains no alpha. If the preselected independent source is technically unavailable, document the failure and close Phase095 before selecting another family/source in a separately preregistered phase.

## Candidate source selection rule

Before implementation, select exactly one public source based only on documented historical availability and timestamp/provenance properties. Do not compare candidate sources using correlation with future returns or any PnL. Preference order: public exchange archive/API with historical positioning/open-interest; otherwise an immutable public derivatives dataset with documented timestamp semantics.

## Isolation

Only `v98_independent_*` namespaced files may be created/modified. Do not modify V16 Frozen, V99 Frozen, V99 workflows/reports/state, or paper state. Phase083 and all 2026 observations remain forbidden for selection. Current V98 Independent champion remains **none** pending a future candidate that passes the complete frozen research protocol.
