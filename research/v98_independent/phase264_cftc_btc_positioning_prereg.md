# V98 Independent Phase264 — CFTC Bitcoin CME Positioning DATA_ONLY

Status: **PREREGISTERED / DATA_ONLY / ZERO ALPHA / ZERO PNL**.

## Independent information class

Phase264 tests weekly regulated institutional positioning in CME Bitcoin futures using the CFTC Legacy Futures-Only Commitments of Traders archive.

This is a new V98 information class distinct from Binance positioning, funding, open interest, trader ratios, price/volume, macro, on-chain, developer activity and network security.

## Frozen market identity

CFTC market:
- market name: BITCOIN - CHICAGO MERCANTILE EXCHANGE
- CFTC contract market code: **133741**
- report family: Legacy Commitments of Traders, Futures Only.

The code/name are frozen before archive retrieval. No alternative crypto contract, exchange, micro contract, Friday futures contract or futures-and-options-combined report may be substituted.

## Frozen source

Official CFTC Historical Compressed annual Legacy Futures-Only text archives:

- 2023: https://www.cftc.gov/files/dea/history/deacot2023.zip
- 2024: https://www.cftc.gov/files/dea/history/deacot2024.zip
- 2025: https://www.cftc.gov/files/dea/history/deacot2025.zip

For each ZIP:
- use the single comma-delimited text/CSV member containing the annual Legacy Futures-Only dataset;
- parse by CFTC header names;
- retain only rows whose stripped `CFTC_Contract_Market_Code` equals `133741`.

No Socrata source, HTML scraping, alternate archive family, alternate contract, or provider rescue inside Phase264.

## Frozen normalized fields

For each retained report date:
- report_date
- open_interest
- noncommercial_long
- noncommercial_short
- noncommercial_spreading
- commercial_long
- commercial_short
- nonreportable_long
- nonreportable_short

All are raw CFTC reported contract counts, no derived signal.

## Integrity gates

Training period only: report dates 2023-01-01 through 2025-12-31.

PASS_DATA_ONLY requires all:

1. all three annual ZIP downloads succeed and each raw ZIP SHA-256 is recorded;
2. exactly one deterministic text/CSV member is selected from each ZIP;
3. at least 50 Bitcoin CME report rows in each calendar year;
4. at least 150 report rows total;
5. no duplicate report date;
6. all retained numeric position fields are integer >=0;
7. open interest >0 for every row;
8. noncommercial/commercial/nonreportable long/short fields do not exceed a loose accounting sanity ceiling of 2x open interest individually;
9. every retained row has contract market code 133741;
10. every retained row's market name contains BITCOIN and CHICAGO MERCANTILE EXCHANGE;
11. no retained date outside 2023-2025;
12. maximum gap between consecutive report dates <=14 calendar days;
13. normalized CSV SHA-256 recorded;
14. deterministic member/hash ledger recorded;
15. two independent acquisitions in one workflow produce byte-identical normalized CSV and manifest;
16. zero crypto price/return join;
17. zero signal direction/window/threshold selection;
18. zero parameter search;
19. zero PnL/backtest;
20. validation/holdout untouched.

Any mandatory failure => **FAIL_DATA_NO_ALPHA**.

## Causality contract

If Phase264 passes, a future separately preregistered economic phase may only use a report after its historically applicable public release delay. The economic phase must explicitly lag weekly positioning rather than assuming report-date availability.

Phase264 itself computes no direction or PnL.

## Isolation

Only V98 Independent namespace/branch.
Phase083 selection use forbidden.
2026+ data forbidden.
V14/V15/V99 not used.
