# V99 I1 — immutable position contract identity binding (pre-code, 2026-10-26)

## Falsifiable failure mode
The research-only native-coin Wallet.check validates high/low and expiry as detached values but does not bind them to the literal short_symbol/long_symbol. A forged deserialized Position could carry a different short strike, long strike, expiry or asset in its symbols than the high/low/expiry fields used for inverse-coin delivery; mark_to_exit would accept quotes matching the forged symbols while settle_batch would pay using the detached numeric fields. This permits a source-to-payoff accounting identity mismatch even though all individual numbers are finite.

## Fixed corrective rule (before code)
For **every** open Position, on **every** Wallet.check, parse both exact Deribit PUT identifiers ASSET-DDMMMYY-STRIKE-P. Both must equal wallet.asset, same expiry at 08:00 UTC, and the parsed short/long strikes must exactly equal Position.high/low; both parsed expiries must exactly equal Position.expiry_ms. Reject malformed/non-string, mismatched asset, strike, expiry, or call identifiers with INVALID_OPEN_COIN_POSITION. No fallback, implicit remapping, float tolerance, economic retune or historical result changes.

## Required falsification and acceptance
Exercise forged short strike, long strike, asset, expiry, call and malformed symbol through Wallet.check and account_nav/settle_batch entry guards. Keep existing two-scenario independent synthetic event-journal oracle and overlapping/atomic settlement tests green. Only code/tests/docs on research branch; no original data, sealed validation, final holdout, Frozen, paper, champion or orders. A green CI is model-accounting integrity only, **not** historical economic TRAIN or validated ROI. This correction is orthogonal to missing licensed BTC+ETH 2021–2023 original option lifecycle data and dated native account terms.
