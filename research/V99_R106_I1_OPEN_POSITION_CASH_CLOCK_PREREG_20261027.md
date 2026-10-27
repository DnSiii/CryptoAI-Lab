# V99 I1 — preregistered open-position CASH decision invariant (2026-10-27)

**SOURCE_ONLY/HOLD; NO PROMOTION.** Existing fixed I1 vertical strategy is unchanged. This is a safety/accounting correction, not a new alpha search. The existing fixture decision adapter validates the wallet's stored last timestamp but can return a nominal CASH decision while open positions have not been marked at the current Monday decision. Such a decision cannot be treated as a complete portfolio state.

## Frozen before implementation

1. Any Monday decision earlier than the wallet's last event timestamp fails with `DECISION_TIME_REVERSAL`, including NO_PREMIUM/no-quote CASH.
2. If any position remains open at a Monday decision, require **all** positions to have same-decision-clock, same-index, independently valid exit-liability marks and an account NAV satisfying maintenance, even if the signal is negative or no new contract is eligible. Missing/stale/mismatched marks fail closed with `PREDECISION_ALL_POSITION_MARKS_REQUIRED`. Never infer an unchanged wallet is a fully valued cash portfolio.
3. An empty wallet can remain in cash without a mark. Existing fixed contract selector, strikes, tenor, scenario fee floors and risk veto are **unchanged**.
4. Independently reproduce the cash clock, position/mark completeness, mark liabilities and maintenance check without importing the primary accounting/selector, and include adversarial controls for stale/absent/forged marks, future wallet clock, and a correctly marked open wallet.
5. Run the existing GitHub Actions fixture gate and original-source veto. This correction cannot unlock historical economics, ROI, validation/holdout, Frozen, paper or orders.

The original 2021–2023 BTC/ETH options complete executable quote and original fee/margin/delivery archive is still missing. No synthetic PASS is a market-performance PASS.
