# V13 original-notional field semantics: source-code trace (2026-11-21)

## Verified source

In `scripts/paper_once_v13.py`, `build_ledger` assigns `order_value_brl` as `round(to_brl(abs(float(result.asset_order_notional.loc[timestamp, symbol]))), 2)` and `order_value_brl_unrounded` as `to_brl(abs(float(result.asset_order_notional.loc[timestamp, symbol])))` (lines 335–347, research branch). Both are derived from the **same model notional**, not independent exchange fill receipts. Therefore a freshly generated, unmodified row should satisfy a two-decimal rounding comparison; however, that comparison alone does not certify execution.

The historical continuity guard `assert_historical_orders_unchanged` (lines 108–138) compares displayed order fields on existing timestamps and checks raw notional only if the previous ledger already had that field. It explicitly does not manufacture precision fields for older rows. `checkpoint` (lines 141–147) refuses to overwrite historical orders on drift. Preserve this behavior.

## Actual ledger evidence and remaining uncertainty

The read-only CI run [44881558881](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/44881558881) classified 1,701 adjustments: 1,425 positive displayed values with no raw field, 272 raw/display mismatches, 3 positive matching raw, and 1 independently represented subcent (decision 681, BTCUSDT, raw BRL 0.0022489215690293693). One mismatch: decision 681 ETHUSDT displayed BRL 7.81 versus raw BRL 7.7148818969287944. This **cannot** be explained by ordinary two-decimal rounding of the currently displayed raw field; the difference is approximately BRL 0.0951181031. It does not prove fraud, an invalid fill, or a particular transformation without a dated upstream receipt.

## Next necessary experiment (no historical mutation)

1. Locate the exact published ledger revision and corresponding generating commit, input snapshots, `to_brl` conversion rate, and model notional for decision 681 (both BTCUSDT and ETHUSDT). Record hashes, timestamps, and source links.
2. Compare the published `order_value_brl` with that original revision's calculation and compare any later precision field with its own original calculation; determine whether raw and displayed fields were produced by **different generations** or currency-conversion states. Do not assume either.
3. Independently reconcile all 272 mismatches and document why 1,425 legacy rows have no raw field. Keep the published ledger immutable; if original evidence cannot be recovered, mark those rows unverified and keep the provenance gate failing closed.

No economic promotion, no retroactive trade reconstruction, no holdout access, no orders. The existing CI fail-closed result is a correct safety outcome, not a successful provenance certification.
