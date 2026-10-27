# V99 I1 — independent fixture OPEN state-integrity correction (preregistered 2026-10-27)

Status: SOURCE_ONLY/HOLD, NO PROMOTION. This is a verifier integrity correction, **not** a new strategy, economics or ROI.

## Defect and fixed acceptance before implementation
The independent I1 fixed-vertical oracle currently checks entry cash, reserve delta, two symbols and quantity, but does not independently bind the newly appended position's expiry/strikes, entire wallet invariants, timestamp, settled history, marks or immediate severe/supersevere maintenance after exit friction. A forged OPEN record could therefore be reported as independently matched despite materially different liabilities or account state.

For a fixture OPEN, independently assert (without importing the primary selector/wallet arithmetic): (1) empty, unmarked before-wallet; valid unchanged asset/scenario/initial coin, no fabricated prior settlements; (2) new position exactly matches selected short/long IDs, same expiry, literal strikes, positive 1-lot quantity, and valid initial >= maintenance > 0; (3) exact cash and reserve deltas, nonnegative cash >= reserve; (4) no invented marks or settlement mutations; (5) last clock equals signal decision; (6) immediate two-sided exit liability plus independently calculated scenario-specific exit fee/slippage floors leaves maintenance covered. Use Decimal and fail closed on nonfinite or altered state. Do not change strategy parameters or the historical sample, do not open validation/holdout, never enable orders.

Add adversarial fixtures that tamper with expiry, strikes, timestamps, settlement history, marks, collateral and maintenance; require oracle failure. Execute existing GitHub Actions workflow, collect actual test results and original-source veto. If the source remains absent, report 0 original synchronized lifecycles and no economic TRAIN. Preserve V16/V99 Frozen, paper/results, champion and dashboard.
