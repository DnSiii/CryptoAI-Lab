# V99 R106 — Phase132 rejection / Phase133 preregistration

## Phase132 decision
Phase132 Cross-sectional Volatility-of-Volatility Reversal is permanently rejected at the preregistered severe train-only gate. It produced 0/4 healthy temporal folds, negative robust mean after removing the top 1% hours in every fold, and negative aggregate train expectancy. No sign flip, window tuning, threshold search, or holdout inspection is permitted as a repair.

## Failure mechanism audit
Phases 126–132 repeatedly show that direct cross-sectional transforms of each asset's own price/volatility state are not overcoming severe hourly friction. Phase132 is materially less catastrophic than several earlier attempts (PF ~0.868 rather than ~0.2–0.6), but its loss is broad across all chronological folds rather than tail-dependent. The next test therefore changes the information object rather than retuning Phase132: dispersion of *idiosyncratic residual returns* after removing the contemporaneous causal market component.

## Phase133 — Idiosyncratic Residual Dispersion Continuation
Preregistered before any Phase133 PnL is computed.

Single frozen hypothesis:
- input: hourly close log returns, train-only; no holdout parsing;
- causal market return at hour t: cross-sectional median hourly return using only assets available at t;
- idiosyncratic residual: asset hourly return minus that market median;
- feature: rolling 24h RMS of idiosyncratic residuals divided by its own trailing 168h rolling median baseline;
- transform: log ratio, then cross-sectional robust median / (1.4826 * MAD), requiring at least 8 assets;
- direction: continuation of relative idiosyncratic dispersion (positive score for unusually elevated asset-specific dispersion, negative for unusually compressed dispersion);
- bounded score: tanh(z);
- execution causality: shift the complete score by exactly 1 hour (t-1);
- normalize each hour to L1=1 before applying the fixed alpha sleeve gross 0.20;
- severe cost gate first; four chronological temporal folds; robust mean excluding top 1% hours;
- no grid, no alternative windows, no sign flip, no threshold search, no post-result repair.

Frozen windows: residual-RMS 24h; own baseline 168h. These are the only Phase133 windows.

Decision gate: PASS only under the existing stable-train diagnostic and temporal-fold requirements. PASS freezes the exact specification for supersevere costs, regime matrix, tails/concentration, benchmark envelope and reproducibility before any untouched holdout. FAIL is permanent for this exact hypothesis.

Integrity requirements remain unchanged: V16 Frozen and V99 Frozen SHA snapshots before/after execution, chronological train-only selection, t-1, post-train targets exactly zero, and untouched holdout.
