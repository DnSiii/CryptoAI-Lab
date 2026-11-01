# V99 I1 signed OPEN immediate native CLOSE reserve — preregistration (2026-11-01)

## Predeclared defect and scope
The signed nonfixture OPEN path currently validates historical native *entry* fees, but its immediate post-entry maintenance check reserves only the modeled severe/supersevere exit-fee floor. When the dated signed native *closing* fee exceeds that modeled floor, the wallet can accept a position that would fail immediate bid/ask close plus the native fee. This is a solvency/risk-accounting defect, not an alpha change.

## Fixed implementation rule before code
For each signed nonfixture OPEN, use the SAME independently signed original OPEN event, full executable short-ask/long-bid quotes, account-tier schedule bytes, timestamp, asset and native lots. Recompute the two-leg native hypothetical close fee using the existing MARK fee formula and independently reexecute it with the separate no-production-import oracle. The hypothetical close is NOT a fill. Use max(modeled severe/supersevere exit fee floor, independently verified native hypothetical close fee) + modeled exit slippage + original adverse bid/ask close liability in the postentry maintenance veto BEFORE returning any mutated wallet. No reuse of rejected alpha, no extra tuning, no validation/holdout data.

## Acceptance / rejection
Adversarial synthetic regression must show a near-boundary signed OPEN that passed the old scenario-only check but now fails the historical native-close reserve; sufficiently collateralized signed OPEN must still pass. Missing or corrupted signed schedule, tampered primary calculator, absent original archive digest or oracle disagreement fail closed. The signed OPEN source digest must bind the original ask/bid quote sides. Existing fixture semantics remain unchanged. CI must execute wallet and fee suites; success certifies software behavior only. Source HOLD and NO PROMOTION remain until complete licensed 661d originals and account-specific provenance are obtained.

## Explicit nonclaims
No historical exchange fill, fee-tier certification, economic TRAIN, realized paper, ROI, strategy promotion, orders, validation or final holdout. Frozen/legacy champion/paper immutable.
