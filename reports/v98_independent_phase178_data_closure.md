# V98 Independent — Phase178 DATA_ONLY closure

Status: REJECT_DATA_AVAILABILITY_NO_RESCUE

## Harvested evidence

The isolated Phase178 workflow reached execution with branch/namespace guards passing, then failed the preregistered annual coverage gate. Official FRED acquisition returned annual valid counts `2023=67`, `2024=263`, `2025=261`; the fixed gate required at least 240 observations in every year.

## Independent failure audit

This is a scientific data-availability failure, not a transport/parser failure. `BAMLH0A0HYM2` is an ICE BofA series for which FRED now exposes only a rolling three-year window. Consequently, in September 2026 the official feed cannot reconstruct the frozen 2023-01-01..2025-12-31 training window without an external historical archive/license.

The family is also not genuinely new inside V98 Independent: Phase151 already audited `BAMLH0A0HYM2`, and Phase166 explicitly attempted a no-backfill reacquisition of the same series. Phase178 therefore closes without economic/PnL inspection and without any rescue via third-party mirrors, archived observations, interpolation, or altered coverage thresholds.

## Anti-overfit / contamination state

- Crypto PnL inspected in Phase178: NO.
- Validation inspected: NO.
- Final holdout inspected: NO.
- V16/V99 used for selection: NO.
- Coverage gate weakened: NO.
- Third-party historical backfill: NO.
- Economic hypothesis authorized: NO.

Decision: `REJECT_DATA_AVAILABILITY_NO_RESCUE`. Move to a genuinely distinct data family.
