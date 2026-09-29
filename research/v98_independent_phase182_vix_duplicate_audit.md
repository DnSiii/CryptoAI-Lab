# V98 Independent — Phase182 VIX duplicate-family audit

Status: **REJECT_DUPLICATE_FAMILY_NO_RESCUE**

## Audit finding

Before implementing or acquiring Phase182, repository-history inspection found that the exact external observable and training window were already investigated repeatedly inside V98 Independent:

- Phase145: `VIXCLS` DATA_ONLY integrity audit for 2023-01-01 through 2025-12-31.
- Phase156: another VIX DATA_ONLY study.
- Phase163: `VIXCLS` DATA_ONLY integrity gate for 2023-01-01 through 2025-12-31.
- Phase164: preregistered economic `VIXCLS >= 30` risk-off experiment, one-day causal lag, subsequently rejected with no rescue.

Phase163 already established the same causal/data family and Phase164 already consumed it economically. Therefore Phase182 is not genuinely orthogonal despite its preregistration text. Re-running acquisition or inventing a new VIX transformation after seeing the Phase164 failure would increase researcher degrees of freedom and violate the anti-overfit intent.

## Phase164 failure evidence retained

The prior VIXCLS economic test was `REJECT_NO_RESCUE`: aggregate training return about -2.56%, daily Profit Factor about 0.737, 2023 return 0, 2024 slightly negative, 2025 about -2.55%, severe and supersevere both negative. Activation was sparse (13 active observations at the frozen threshold), and tails were highly concentrated. Validation and final holdout were not used.

## Decision

Phase182 is closed **without acquisition, PnL, threshold selection, sign flip, lookback selection, or rescue**. It cannot be used to reopen VIX/VIXCLS research under a new phase number.

The next hypothesis must come from a genuinely new data family not already economically tested in V98 Independent. V16, V99, V99 paper state, and the V98 final holdout remain untouched.
