# V99 I1 — post-entry mark-to-close lower-bound maintenance veto (preregistered 2026-10-26 03:xx BRT)

**SOURCE_ONLY/HOLD, NO PROMOTION.** This is a deterministic accounting safety correction, not a strategy retune, synthetic ROI, execution proof or permission to open validation/holdout. C1 remains rejected.

## Observed code defect and fixed remedy

`open_vertical` checks native cash against initial margin and (for overlapping positions) pretrade marked NAV, but currently accepts a new short-put vertical even when the *same original two-leg book's* conservative immediate mark-to-close liability already puts post-entry NAV below total maintenance. This allows an economically impossible open to be counted until a later mark. In addition, a new vertical may use an underlying index different from the existing open-position marks at the same timestamp.

Precommit **without inspecting any historical PnL**:
1. Require both legs to pass existing strict predecision and <=1s synchronization checks; no change to entry or strategy thresholds.
2. Calculate **minimum immediate closing liability** `max(0, native_lots * (short.ask_coin - long.bid_coin))` from the same original quote pair. This is a **lower bound** (excludes unverified exit fees/slippage); it must never be mistaken for a realized close or authenticated native quote conversion.
3. If overlapping positions exist, require their fresh as-of NAV (existing guard) and **exact same original underlying index** as the new pair; otherwise veto the new open. Compute post-entry NAV lower bound = cash after credited entry premium - existing marked liabilities - new lower-bound closing liability. Veto when this NAV is below existing plus new maintenance requirements. No change to the cash-reserve gate.
4. Independently recompute this lower bound in the Decimal reference journal for every `open` event, and add adversarial controls for an entry that passes cash/initial-margin but fails posttrade maintenance, plus a mixed-index overlapping entry. Existing synthetic two-position replay must continue to match. The reference oracle must never import production accounting.
5. Run actual branch CI, inspect job logs and record failures and final result. **Even all-green synthetic CI cannot certify historical 2021–2023 BTC/ETH options economics.**

External blocking evidence remains original licensed full lifecycle BBO+size and arrival clocks for 182 asset-weeks, dated native lot conversion, account fees, margin/liquidation, delivery receipts. No changes to Frozen, paper, champion, orders or sealed periods.
