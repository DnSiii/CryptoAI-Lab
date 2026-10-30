# V99 R106 — terminal liquidation reconciliation prereg (2026-10-30 11:4x BRT)

## Critical accounting defect / precommitted test
Legacy C1/C2 diagnostic reports last next-open mark NAV but does **not** account for liquidating outstanding contracts at the terminal boundary. This omission can overstate terminal capital for a future complete engine; it does not resurrect either permanently rejected model.

Before reading any new economics, append an **additional, separately named terminal-close diagnostic** to the existing read-only C1/C2 original TRAIN audit. At the already-defined last original next-open timestamp, close every remaining signed contract at the terminal next-open mark. Terminal notional = sum(abs(last_q[j])*last_next_price[j]); terminal close fee = scenario modeled cost per side * terminal notional; liquidated NAV = original last marked NAV - terminal fee. Reject negative/nonfinite terminal notional, fee, or nonpositive NAV; independent verifier must recalculate from the trace without trusting summary fields. Keep the original trace, legacy archived ROI, all cost scenarios, folds and market partitions unchanged. Do not label the liquidated NAV as a new strategy ROI because the frozen target policy was not re-run with corrected self-financing costs.

## Tests and release criterion
Adversarial tests: terminal cost positive for nonzero position; zero for zero exposure; tampered close fee or NAV rejected; final market mark cannot be omitted; independent oracle does not call the implicit rebalance fee solver. Re-run original 16,055-hour x C1/C2 x severe/supersevere accounting on GitHub CI and verify deterministic double replay. Never read validation >=2023-10-01 or holdout >=2024-01-18. No Frozen, paper, champion, legacy outcome or order changes.

## Outcome
Software integrity only. No exchange-native fill, funding, margin or dated fee certification; no candidate promotion. I1 remains blocked on original licensed 658 missing days of executable Deribit BTC/ETH options BBO/size/arrival, marks/settlement and dated native terms.