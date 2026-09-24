# V99 R106 — Phase130 rejection / Phase131 preregistration

## Phase130 decision
Phase130 downside-semivariance asymmetry continuation is permanently rejected on the preregistered train-only gate. Severe train ROI -66.0175%, PF 0.59768, max DD 66.0343%, robust mean ex-top1% -7.0804e-05/hour, 0/4 healthy temporal folds. All four folds are negative. Causality invariants passed, post-train targets are zero, holdout was not parsed, and V16/V99 Frozen remain untouched. No sign flip, horizon change, or repair is permitted for Phase130.

## Phase131 preregistration — Idiosyncratic Volatility Shock Continuation
Scientific rationale: Phases127-130 show that raw/residual momentum, volatility-normalized momentum, short-horizon reversal and downside asymmetry do not survive severe costs. Phase131 therefore tests a distinct state variable: cross-sectional *idiosyncratic volatility shock*, not return direction. The hypothesis is that assets whose short realized volatility expands unusually relative to their own slower baseline exhibit persistent relative opportunity after removing the cross-sectional median state.

Frozen specification before any Phase131 PnL:
- input: hourly close-to-close log returns only;
- short realized volatility: rolling 12h RMS return;
- slow realized volatility: rolling 96h RMS return;
- raw shock: log((RV12 + 1e-12)/(RV96 + 1e-12));
- at each timestamp subtract cross-sectional median shock;
- robust cross-sectional scale: median / (1.4826*MAD), with safe zero handling;
- score: tanh(robust z), continuation direction;
- entire score shifted exactly one hour (`t-1`) before positions;
- minimum 8 valid assets; L1 normalization; alpha gross fixed at 0.20;
- train end exclusive 2024-01-18T00:00:00Z; all post-train targets forced to zero;
- severe-cost train gate plus four chronological temporal folds and robust mean excluding top 1% hourly PnL;
- single hypothesis, no grid, no sign flip, no threshold/horizon/gross search;
- untouched holdout is not parsed during selection;
- V16 Frozen and V99 Frozen are immutable and SHA-checked before/after execution.

Decision rule: PASS freezes this exact specification for supersevere costs, regime matrix, tails/concentration, benchmark envelope and reproducibility before any untouched holdout. FAIL is permanent and Phase131 receives no retuning.
