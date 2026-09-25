# V99 R106 Phase137 — pre-PnL Binance alignment incident and frozen missing-data rule

Date: 2026-09-25
Status: PRE-PNL IMPLEMENTATION CORRECTION / HYPOTHESIS UNCHANGED

The first protected Phase137 workflow aborted before producing a report or evaluating PnL because the runner incorrectly asserted that all five canonical Binance series were complete at every hour of the frozen 2021-12-01 through 2024-01-17 training window.

No Phase137 PnL, return relation, fold result, or sign information was observed.

## Evidence

The existing canonical research manifest shows:

- BTCUSDT: no missing hours.
- ETHUSDT: no missing hours.
- DOGEUSDT: no missing hours.
- SOLUSDT: 120 missing canonical hours, first at 2022-02-26 00:00 UTC.
- XRPUSDT: 120 missing canonical hours, first at 2022-02-26 00:00 UTC.

Each affected series therefore still has more than 99% coverage over the frozen Phase137 window. Phase136 independently proved the OKX side has 100% hourly coverage.

## Frozen handling before PnL

The Phase137 economic hypothesis, 168h lookback, mean-reversion direction, five-symbol mapping, t-1 lag and 0.20 gross remain unchanged.

The implementation rule is now frozen as follows:

1. Never fill/interpolate missing Binance prices.
2. Compute each venue spread only where both same-hour prices are present.
3. Rolling median/MAD use only naturally available observations and retain the frozen 168-observation minimum; a gap therefore delays that asset's eligibility rather than being filled.
4. Require at least 4 contemporaneously valid cross-sectional asset scores. If fewer than 4 are available, the entire cross-sectional alpha is zero for that hour.
5. No symbol substitution is allowed.
6. Persist per-symbol Binance coverage/missing counts in the Phase137 report.
7. Abort pre-PnL if any frozen Binance symbol has <98% coverage in the frozen training window.

This is a data-integrity correction after a pre-PnL assertion failure, not rescue tuning after a result.
