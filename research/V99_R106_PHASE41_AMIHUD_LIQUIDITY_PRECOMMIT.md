# V99 R106 Phase 41 — Cross-sectional Amihud Liquidity Alpha

Status: PRE-REGISTERED / TRAIN-ONLY SELECTION

Hypothesis: a cross-sectional liquidity-premium signal based on lagged Amihud illiquidity (`abs(return)/quote_volume`) is structurally distinct from phase29's transient liquidity-shock reversion and phase33's quote-volume trend. Test whether persistent lagged illiquidity ranking carries severe-cost alpha.

Locked families before execution: 24h, 72h, 168h rolling Amihud means. Higher illiquidity is long, lower illiquidity is short. Fixed TOP_N=2 each side and fixed alpha gross=0.20, using the existing causal cross-sectional risk-normalized weighting/rebalance machinery.

Validation lock: features shift t-1; chronological train-only selection; no parameter grid; severe-cost selection; temporal folds; untouched holdout may be evaluated only for a family that first passes the locked train gate. A passing holdout is still insufficient for promotion: supersevere costs, regime matrix and benchmark envelope remain mandatory.

V16 Frozen and V99 Frozen must not be modified.