# V98 Independent — Phase240 postmortem

Decision: **REJECT_FAMILY_NO_RESCUE**.

Phase240 tested preregistered lagged idiosyncratic shock-recovery relative value. The decision-grade workflow rebuilt training-only data through 2025-12, passed the <2026 firewall, causal/grid/funding invariants, and produced two byte-identical evaluator outputs (workflow SHA256 `8aa73d855bfad3a635f28b0906d444b1ac0ec58530df39746397827faab68b76`). The independent validator rejected all eight frozen specs.

## Failure mechanism

This is not a marginal transaction-cost failure. Representative `idsr_beta168_scale168_k1_h4` is already catastrophically negative at base cost in 2023: return -99.4355%, max drawdown -99.4724%, Profit Factor 0.5250, payoff 0.8992, win rate 36.83%, positive days 11.23%. Bear, bull, and sideways returns are all negative (-63.48%, -80.43%, -92.10% respectively), so no observed regime supports a scientifically legitimate rescue filter. Severe cost further deteriorates the path.

Asset contribution is broadly negative across BTC/ETH/BNB/XRP/SOL rather than being explained by one isolated asset; max asset concentration is only ~20.97% in the representative 2023 base case. Funding contributions are small relative to the trading loss, so funding is not the cause. Turnover is very high (L1 6700.25) but the edge is negative before severe/supersevere stress; reducing costs after observing the result would therefore be both insufficient and an impermissible rescue.

The hypothesis that large standardized idiosyncratic residual shocks exhibit exploitable cross-sectional recovery at the frozen horizons is rejected. No sign flip, threshold rescue, regime filter, asset deletion, or opened-holdout tuning is permitted.

## Scientific consequence

Phases 236–240 collectively provide strong evidence against continuing to mine nearby residual distribution/persistence/shock-recovery transforms. The next experiment should move to a genuinely orthogonal information family rather than another residual-moment variant. Holdout 2026+ remains unopened; V16/V99 and V99 paper state are untouched.
