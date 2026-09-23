# V98 Independent — Phase121 CFTC CME Bitcoin positioning DATA_ONLY preregistration

Status: FROZEN BEFORE DATA INSPECTION / ZERO PNL.

## Scientific family
Test whether official CFTC historical Commitments of Traders financial-futures files provide sufficiently complete weekly CME Bitcoin futures positioning records for the frozen 2023-2025 training era. This is institutional regulated-futures positioning and is distinct from crypto-exchange funding/OI, sentiment, stablecoin supply, DeFi activity, WALCL, and prior price/volume families.

## Frozen source and frame
- Source: official CFTC annual historical financial-futures COT archives (`fut_fin_txt_2023.zip`, `fut_fin_txt_2024.zip`, `fut_fin_txt_2025.zip`).
- Instrument identification: market name must contain `BITCOIN` and exchange name/market label must identify Chicago Mercantile Exchange/CME. No substitute instrument if absent.
- Training frame only: report dates 2023-01-01 through 2025-12-31.
- DATA_ONLY output may persist row/date counts, coverage, schema presence, duplicate/invalid counts and payload/date-index SHA256 hashes only. It must not persist trader-position values, descriptives, transformations, correlations, crypto returns, alpha or PnL.
- No interpolation/fill and no alternate CFTC report family if the frozen financial-futures archives fail.

## Gate
`PASS_DATA_ONLY` requires all three annual archives to download successfully, the frozen Bitcoin/CME instrument to be identifiable, at least 95% coverage versus expected weekly observations across the training frame, zero invalid report dates and zero duplicate canonical report dates. Otherwise `REJECT_DATA_SOURCE_NO_RESCUE`.

## Isolation
Validation and final holdout remain closed. V16 Frozen, V99 Frozen, all V99 research/workflows/reports/paper state are forbidden as evidence or tuning input. A pass authorizes only a separately preregistered economic hypothesis before any position values are inspected for alpha/PnL.
