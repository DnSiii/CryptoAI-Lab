# V99 I1 — Signed MARK exit-fee provenance veto (preregistered 2026-11-01)

## Predeclared defect and scope
The nonfixture costed_mark path verifies an original MARK signature and modeled severe/supersevere friction floors, but it does not apply the already signed historical account-tier fee schedule to the executable CLOSE sides (short ask, long bid). If a dated native close fee exceeds the modeled floor, NAV and the maintenance check can be overstated. This is a critical-path accounting defect, not an alpha change.

## Fixed repair, before looking at results
On every nonfixture MARK, after source signature authentication and before changing wallet marks, reuse the existing signed dated fee schedule and independent per-leg oracle. Interpret MARK as a hypothetical two-leg close (short ask, long bid) with the same dated entry/exit fee rate and legwise premium cap; never treat it as an executed fill. Require actual modeled mark exit fee >= both the native schedule minimum and the scenario floor, and slippage >= scenario floor. Preserve t-1 receipt constraints and existing exact event digest. Never modify OPEN/SETTLE accounting, TRAIN candidate parameters, validation/holdout, Frozen, paper, champion or place orders.

## Adversarial tests and decision
Add a dated-fee MARK test where the historical fee floor exceeds scenario floor and rejects an undercharged NAV, another where full fee passes, a primary fee calculator tampering test caught by independent oracle, and a signed wallet MARK mutation veto test. Run real GitHub CI and inspect results. If licensed 661d original books and account-tier/fill/margin documents are absent, status remains SOURCE HOLD — NO PROMOTION; zero certified lifecycles, no ROI. This only improves software readiness.