# V99 R106 — Phase177 pre-PnL failure-mechanism audit

Date: 2026-09-29
Scope: independent scientific audit before data admission; no returns inspected.

## Main failure risks

1. **Trade sparsity masquerading as volatility state.** Historical option trades are event-driven. A last-trade IV can become stale exactly when the market moves fastest. Therefore a reconstructed hourly state cannot silently forward-fill across arbitrary gaps; staleness must be explicit and coverage-gated.
2. **Selection on instruments that happened to trade.** Choosing only traded strikes can create endogenous liquidity selection. The preregistered nearest-forward-ATM rule must be applied to the contemporaneously listed admissible universe, and absence of a usable observation must remain missing rather than switching to a more convenient strike.
3. **Underlying/moneyness lookahead.** A current or retrospectively reconstructed index value cannot be paired with an older option trade. Underlying state used for moneyness must itself have an event/availability timestamp no later than the option-state decision cutoff.
4. **Expiry-boundary instability.** Around expiry rolls, the two contracts bracketing 30 days can change abruptly. The interpolation rule is fixed, but discontinuities and missing brackets must be reported by month/fold rather than patched.
5. **Modern metadata leakage.** Current instrument catalogs or modern DVOL values cannot prove historical point-in-time availability. Historical reconstruction must be based on contemporaneous first-party observations plus exchange metadata whose historical meaning is established.
6. **Tail/concentration illusion.** If the data gate eventually passes, aggregate TRAIN ROI alone is insufficient. Any alpha must undergo the existing temporal folds, severe/supersevere costs, regime matrix, benchmark envelope, top-tail removal and concentration audits before promotion.

## Decision

These risks do not justify changing the preregistered construction. They strengthen fail-closed requirements. Phase177 remains DATA/INTEGRITY-only until complete first-party TRAIN coverage and causal inputs are demonstrated. If coverage is structurally sparse, reject rather than tune staleness thresholds after observing PnL.

No holdout access. V16 Frozen and V99 Frozen untouched.