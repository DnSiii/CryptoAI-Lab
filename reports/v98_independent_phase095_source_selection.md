# V98 Independent Phase095 — frozen source selection

Status: **SOURCE SELECTED BEFORE ALPHA / NO PNL**

The Phase095 preregistration requires exactly one independent provider/source to be selected using only documented historical availability and timestamp/provenance properties.

## Selection

Selected family/source: **CandleFeed aggregated liquidation history, Bybit venue, daily cadence**, targeting BTCUSDT and ETHUSDT over 2023-01-01 through 2025-12-31.

Reason for selecting liquidation rather than open interest: public provider coverage documentation indicates that non-Binance open-interest archives discovered in this cycle begin too late for the frozen 2023-2025 feasibility window (for example, CryptoHFTData OKX OI begins 2025-06-28 and CandleFeed reports Bybit/OKX OI only from 2026). CandleFeed documents aggregated Bybit liquidation history from 2020, which is chronologically capable of spanning the required training window and is a different information family from the Binance OI/positioning data consumed in Phase047.

This selection is based solely on advertised data coverage. No price returns, correlations, directional rule, PnL, validation, Phase083, or 2026 observations were inspected to choose it.

## Frozen implementation target

Audit daily aggregated liquidation records only. Required fields/properties to verify before any future hypothesis may be written: provider timestamp/period semantics, BTC/ETH coverage through 2023-2025, deterministic ordering/deduplication, missing-period fraction, invalid timestamps, provenance, and reproducible acquisition from GitHub Actions without committed credentials.

If historical acquisition requires a paid/private credential unavailable to the workflow, or the advertised coverage cannot be reproduced, Phase095 closes as `FAIL_DATA_NO_ALPHA`. Do not switch to another source inside Phase095.

## Isolation

Only V98 Independent namespaced artifacts may use this selection. V16/V99 and Phase083 remain untouched and forbidden for selection. Current V98 Independent champion: **none**.
