# V99 I1 — original OPTIONS entitlement fail-closed correction (preregistered 2026-10-27 15:xx BRT)

## Critical defect and economic consequence
The authenticated Tardis `/v1/api-key-info` grant includes `dataPlan`, but `_scope_covers_train` currently ignores it. A Deribit **perpetuals-only** grant with `symbols: []`, or even a contradictory `symbols: ["OPTIONS"]`, can be accepted as an all-options historical entitlement if the date range is wide enough. This creates a false-positive procurement/source readiness signal and can waste a paid subscription. No original market archive has been obtained.

## Fixed acceptance rule BEFORE code/test
A grant must simultaneously match Deribit, cover 2021-12-09 through 2023-10-01 exclusive, grant all option symbols (empty symbols or the literal OPTIONS group), **and** explicitly identify an option-inclusive plan. Accept only unambiguous normalized `dataPlan` values `options`, `derivatives`, `all-exchanges`, `all_exchanges`, `unlimited`; reject `perpetuals`, `spot`, absent, unrecognized and malformed values, even when symbols claim OPTIONS. No fuzzy substring inference. A valid grant plus three bounded 206/gzip probes remains ACCESS_PROBE_ONLY, not full source/fee/margin/fill certification.

## Adversarial checks
Positive: documented unlimited, explicit options, derivatives, all-exchanges with full date/symbol grant. Negative: perpetuals with empty symbols, perpetuals with OPTIONS symbol group, unknown or absent plan, finite two-contract list, short date, wrong venue. Assert no paid data request after a failed scope and never expose key. Reexecute GitHub Actions and harvest results.

## Procurement alternative verified in official vendor documentation
Tardis billing FAQ documents an **Options** plan including Deribit (not necessarily the more expensive Derivatives plan); annual bank-transfer invoicing adds 12 months to ordinary 4-year annual history (nominal five years), and the historical starting date is anchored to **invoice issuance**, not when the transfer settles. The exact pricing, entitlement, BTC/ETH quote fields, contract completeness, licensing, native historical fees/margins and settlement receipts remain unverified. Do not buy or claim execution readiness from these pages.

Official sources: https://docs.tardis.dev/faq/billing-and-subscriptions and https://docs.tardis.dev/historical-data-details/deribit.md and https://docs.tardis.dev/api/http-api-reference .

## Invariants
SOURCE_ONLY/HOLD, NO PROMOTION. No orders; no validation >= 2023-10-01 or final holdout; no Frozen/paper/champion modifications. This change does not constitute an economic TRAIN or claim of ROI.
