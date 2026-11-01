# V99 I1 — signed-wallet dated native-fee binding (preregistered 2026-11-01)

## Scope and non-negotiable boundaries

TRAIN only, fixed I1 strategy, 2021-12-09 through 2023-09-30. Do not inspect sealed validation, final holdout, Frozen, champion or paper. This change is **execution-accounting wiring**, not a new alpha candidate, historical proof, new TRAIN return or permission to trade. The existing severe/supersevere paths and fixed 180 intent grid remain unchanged.

## Problem and fixed implementation

The existing signed wallet event adapter verifies an independent event attestation and modeled scenario cost floor, but does **not** invoke the separately implemented historical dated fee preflight on the actual signed OPEN and SETTLE_BATCH wallet debit. Thus a signed event with a lower-than-dated native fee can enter provisional NAV. Require the signed dated-fee preflight in the actual costed wallet operations **before** mutating cash or positions.

For signed nonfixture OPEN, bind the identical canonical `event_digest("OPEN", wallet, ...)` and exact expected original archive manifest SHA256 already used by the source gate. Derive the native fee minimum from the two executable original quote sides (short **bid** and long **ask**), the actual wallet scenario, event UTC clock, asset and actual native lot quantity. Require charged fee >= max(original dated native fee, fixed scenario fee floor) and charged slippage >= modeled scenario slippage floor. Do not use midprice or inferred discounts.

For signed nonfixture SETTLE_BATCH, first validate the complete atomic due cohort and its native wallet positions. Bind the **same whole batch event digest and original archive SHA256** to each position's original strike pair, expiry clock, actual native quantity, original contractual delivery index and individually charged settlement fee. Require each fee >= max(dated native settlement fee, fixed scenario settlement fee floor), with zero contractual settlement slippage (no synthetic exit fill). Any missing signed historical account tier/interval, source mismatch, or missing expected archive digest fails closed before NAV. MARK remains a hypothetical two-sided exit cost bound, **not** a historical executed fee certificate.

Only execute this new historical preflight for `fixture=False`; fixture accounting and existing scenario-floor tests must remain unchanged. Existing synthetic signed-adapter tests may mock **only** this new additional dated-fee check to retain coverage of event-signature wiring; they must never be represented as historical certification. New adversarial tests must prove OPEN and each SETTLE_BATCH position are checked, insufficient fees fail before wallet changes, missing manifest is rejected, and no promotion flags are set.

## Decision and evidence

Run independent arithmetic suite, wallet suite, signed adapter suite and integrated GitHub Actions. Even if all pass: **SOURCE HOLD — NO PROMOTION** until the independently authenticated full 661-day original BTC/ETH options archive, native historical account-tier schedule, fills/quotes/contract lots, delivery index, margin/liquidation provenance, five chronological folds, both stress scenarios, independent reexecution and all economic gates are actually available and pass. No order submission, invented PnL, or changes to historical records.
