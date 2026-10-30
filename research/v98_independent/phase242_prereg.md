# V98 Independent Phase242 preregistration — illiquidity/price-impact reversal

Status: PREREGISTERED, NOT EXECUTED. Phase241 performance remains unobserved at preregistration.

## Scientific distinction
Test whether unusually large lagged price movement per unit of traded quote volume identifies transient price impact that subsequently reverses cross-sectionally. This is distinct from Phase241: Phase241 multiplies abnormal quote-volume by lack/opposition of 24h price confirmation; Phase242 measures absolute price impact per dollar of quote-volume and uses the signed lagged return only to define reversal direction.

## Firewall and causality
- Training/evaluation only through 2025-12-31 23:00 UTC; 2026+ untouched.
- Decision at open(t) uses only bars through t-1.
- No V99 evidence, reports, state, workflows, parameters, or selection.
- No post-result sign flip, threshold rescue, asset deletion, regime gating, or grid expansion.

## Frozen construction
For asset a and hour u:
1. one-hour close return r1(u)=close(u)/close(u-1)-1.
2. impact raw I(u)=abs(r1(u))/max(quote_volume(u),1e-12).
3. causal own-history normalization uses log1p(I) relative to rolling median and rolling MAD ending at u-1, MAD floor 1e-9.
4. decision t reads normalized impact(t-1) and sign(r1(t-1)).
5. score(t) = -sign(r1(t-1)) * normalized_impact(t-1): high positive score means large positive impact is faded; large negative impact is bought.
6. rank cross-sectionally, long top k / short bottom k, equal weight, dollar neutral, gross <=1.
7. no regime gate.

## Frozen grid
- normalization window iw in {168,336} hours
- k=1
- holding H in {4,8} hours
Total: 4 specs.

## Evaluation and gate
Use chronological 2023/2024/2025 folds, PIT funding, and costs 7/14/28 bp per unit turnover. Report return, max drawdown, Profit Factor, payoff, win rate, positive days, turnover, funding, asset contribution/concentration, daily p01/p05/p50/p95/p99 and best/worst day, plus bull/bear/sideways diagnostics.

Promotion requires one frozen spec to pass in every fold: base return>0, PF>1, max drawdown>=-35%, positive days>50%; severe return>0 and PF>1. Supersevere remains mandatory diagnostic. Deterministic byte-identical rerun and independent validator are required before promotion. Otherwise REJECT_FAMILY_NO_RESCUE.
