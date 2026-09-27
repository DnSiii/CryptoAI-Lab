# V98 Independent — Phase168 Treasury General Account DATA_ONLY preregistration

Date: 2026-09-27

## Scope
Fresh orthogonal macro/liquidity data family: U.S. Treasury General Account (TGA). DATA_ONLY only. No economic PnL, no validation/final-holdout access, no V99/V16 dependency.

## Scientific rationale
TGA is a direct U.S. fiscal-liquidity stock and is economically distinct from previously rejected HY spread, RRP, CFTC BTC positioning, broad-dollar/DXY, NFCI and VIX families. This phase tests only whether a deterministic, sufficiently complete point-in-time source can be established before any economic hypothesis is permitted.

## Frozen source candidate
Primary official/public series candidate: FRED `WTREGEN` (Treasury General Account: Wednesday Level). The native weekly frequency must be preserved; no daily interpolation, forward fill, backfill, or synthetic observations are permitted in this DATA_ONLY phase.

## Frozen window
2023-01-01 through 2025-12-31 inclusive. Do not inspect validation/final holdout.

## Pre-registered integrity gates
1. Acquire the same source independently twice and require byte-identical canonicalized output SHA-256.
2. Parse date/value strictly; reject malformed, duplicate-date, non-finite, negative, or out-of-window observations.
3. Preserve native weekly timestamps and chronology.
4. Require >= 95% global coverage versus expected weekly Wednesday observations in the frozen window and >= 90% coverage in each calendar year.
5. Record observation count, first/last date, missing rows, duplicate dates, malformed rows, non-finite values, negative values, out-of-window rows, global coverage and annual coverage.
6. Deterministic replay must reproduce the exact canonical output and SHA-256.

## Economic firewall
No return/PnL calculation, no correlation-to-crypto inspection, no threshold selection, no sign choice, no lag search, no regime optimization and no rescue are allowed in Phase168. An economic Phase169 may be preregistered only after Phase168 independently passes every DATA_ONLY gate and freezes the exact data hash.

## Failure policy
Any gate failure => `REJECT_DATA_QUALITY_NO_RESCUE`. Do not relax coverage gates after seeing evidence, trim the frozen window, impute, carry forward, backfill from another phase, or substitute a different series under the same phase number.

## Isolation
Only V98 Independent namespaced artifacts may consume this preregistration. V16 Frozen, V99 Frozen, V99 research/workflows/reports and V99 paper state are out of scope and must remain untouched.
