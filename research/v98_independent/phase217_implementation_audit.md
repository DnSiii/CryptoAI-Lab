# V98 Independent — Phase217 implementation audit

## Scope
Pre-result audit of `scripts/v98_independent_phase217_serial_sign_persistence.py` against the frozen Phase217 preregistration. No validation/final holdout was opened and no V99 evidence was used.

## Causality
- Hourly close returns explicitly use `pct_change(fill_method=None)`; missing observations are not implicitly forward-filled.
- At decision timestamp `t`, `sign_balance` and majority sign are rolling statistics shifted by one bar, so their latest constituent is the completed return ending at `t-1`.
- Latest direction is `sign(return).shift(1)`, therefore also ends at `t-1`.
- Entry position is written beginning at `t`; PnL uses lagged position against open-to-open return, preventing same-bar execution leakage.
- BTC is excluded from signal generation and appears only in the pre-existing causal regime decomposition, itself shifted one bar.

## Frozen search space
The evaluator contains exactly the preregistered Cartesian product: `L in {6,12}`, `B in {0.50,0.67}`, `hold in {3,6}` = 8 specs. Direction is continuation only. No inversion, asset filter, regime filter, rescue threshold, or additional hyperparameter exists.

## Portfolio / execution invariants
- Universe is ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT.
- At most one live position per asset; signals during a frozen hold are ignored.
- Simultaneous gross exposure is normalized to <= 1.0.
- PIT funding is charged/credited at mapped funding timestamps and is never a signal input.
- Base/severe/supersevere round-trip-equivalent conventions are frozen at 0.07%/0.14%/0.28% and evaluated for every spec/fold.

## Required diagnostics
Each spec × fold × stress records total return, max drawdown, Profit Factor, payoff, win rate, positive days, trade count, best/worst trade, p01/p05/p50/p95/p99 tails, asset attribution/concentration, funding contribution, and bull/bear/sideways regime metrics.

## Data firewall / reproducibility
Workflow rebuilds canonical training data, rejects any price/funding timestamp >= 2026-01-01, checks monotonic/unique timestamps, runs the evaluator twice, compares byte-level SHA256 output, asserts the complete metric schema and monotone cost-stress degradation, then applies the mechanical 2023/2024/2025 training gate.

## Decision before results
Implementation is consistent with the frozen Phase217 protocol. Any failure of the 3-fold base gate rejects the family without inversion/rescue. Any survivor must still clear stress, tails/concentration/regimes, causality/invariants and deterministic reproducibility before validation is considered.
