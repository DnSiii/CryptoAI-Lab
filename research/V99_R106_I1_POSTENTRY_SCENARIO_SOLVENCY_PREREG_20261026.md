# V99 I1 — immediate post-entry severe/supersevere solvency veto (2026-10-26; preregistration before code)

## Defect and fixed test
The existing research-only `costed_open` enforces modeled opening fee/slippage floors, but `open_vertical` checks post-entry maintenance against an optimistic exit liability that excludes the *scenario's mandatory exit fee and slippage*. Consequently, a fixture portfolio can pass a weak collateral lower bound while its conservative executable close NAV is already below maintenance. `costed_mark` can also return a fully marked insolvent wallet unless the caller separately invokes `account_nav`.

## Fixed implementation contract
- Preserve the exact existing severe and supersevere per-leg modeled floors (0.0012 and 0.0024 coin/native lot respectively for BOTH fees and slippage); do not reinterpret them as historical native fees.
- After `open_vertical` computes a proposed immutable wallet, calculate the **immediate** closing liability from the SAME predecision, size-checked two-leg book: `max(0, qty*(short.ask_coin-long.bid_coin)) + minimum modeled exit fee + minimum modeled exit slippage`. Add all existing predecision marked liabilities. Require `proposed.cash_coin - total_exit_liability >= sum(all maintenance_margin_coin)`, otherwise reject with `POSTENTRY_SCENARIO_COST_MAINTENANCE_VETO`. This is a necessary lower bound, NOT a historical liquidation simulation or a guarantee of real fills.
- When `costed_mark` produces a complete synchronized mark set at the same `at_ms`, immediately invoke existing `account_nav` to veto maintenance breaches; incomplete mark sets remain incomplete and cannot be treated as NAV.
- Independent oracle must reproduce the post-entry check from a standalone Decimal journal, without importing primary wallet or cost adapter.
- Adversarial test: a synthetic wallet with initial 1 coin, a credit spread gross .03, severe/supersevere opening costs, maintenance chosen between the weak and stressed closing NAV must be rejected. A separate fully marked maintenance breach must be rejected. Healthy synthetic positions still pass.
- Nonfixture source remains fail-closed. No orders, no original fill/fee/margin certification, no ROI or economic TRAIN, no validation/holdout access, no promotion. Never modify Frozen, paper, champion or legacy records.

## Scientific decision
This repairs a genuine scenario-risk veto. It does **not** remove the missing original 2021-12-09..2023-09-30 BTC/ETH Deribit complete BBO+size/arrival archive, native historical fee tier, original margin/liquidation and settlement evidence. Source-only/HOLD until those independent original receipts are supplied and the five-fold economic TRAIN passes.
