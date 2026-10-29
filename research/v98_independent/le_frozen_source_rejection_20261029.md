# V98 Independent LE — permanent source-only rejection (2026-10-29)

**Decision: REJECT LE; do not rescue, retune, or compute PnL.**

- Pre-registration committed **6126c746392bb241cb8520c11eb17f730cc8be5d** before LE source implementation, source counts, or LE PnL. Source code committed **121724eb48de9fa7ac718603e16a90371793419d**.
- Authenticated original Clean-4 training artifact ID **12549265452**, Dec-2022 warmup through Dec-2024 only: **18,288** hourly bars, **9,144** native signed funding events. SHA256 native funding/bounds **f706812b7989666c3efd0b24045a5c31f4d9c79b46d61da7b5e6cde6c6e73f5e**. Four official OHLC hashes independently checked against original Phase803 receipt. No 2025/2026+, XRP, old holdout, V14/V15/V99 internal data or live orders.
- Source implementation passed synthetic future mutation, real 14,000-hour prefix future mutation, no silent row changes, source quote entry quarantine, and gross budget (observed max intended gross **0.88**, precommitted maximum 0.94).
- **Independent read-only scalar source count** (does not import LE signal code) exactly matched the LE bundle:
  - 2023: Opportunity **10**, Relative Value **4**, Stress/Recovery **9**.
  - 2024: Opportunity **8**, Relative Value **9**, Stress/Recovery **15**.
- **Hard preregistered source failure:** Relative Value in 2023 **4 < 8** minimum activations. LE permanently rejected **before** system PnL. No fee, sign, threshold, event clock, gross, filter, or architecture change to LE allowed. No original 30-cell runner or independent physical PnL performed; no historical performance or profit claims.

Next: create a **genuinely distinct** complete seven-slot hypothesis with its own pre-committed economic drivers and independently validate source before physical economic testing. This rejection is not a validation of a finished V98. Frozen, paper, and holdout unchanged.
