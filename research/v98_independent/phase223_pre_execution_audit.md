# V98 Independent Phase223 — pre-execution audit

Status: audited before any Phase223 result is observed. Phase223 remains contingency-only and MUST NOT execute before Phase222 receives its mechanical disposition.

## Contract verification

- Frozen grid is exactly 8 specs: W={168,336} x K={2.5,3.5} x H={2,6}.
- Signal uses completed return r1(t-1) and rolling sigma through t-1; execution is at open(t).
- The preregistered market-direction filter is implemented literally: same-sign BTC completed 1h move with |BTC r1| >= 0.75% suppresses the candidate.
- Portfolio normalizes simultaneous active assets to gross <=1 and forbids same-asset overlap.
- Turnover costs remain 7/14/28 bp; PIT funding is applied only to lagged open exposure.
- Folds remain exactly calendar 2023/2024/2025 and the loader rejects any timestamp >= 2026-01-01 UTC.
- Closed-trade tails are asset-attributed and include the exit/rebalance row; fold-boundary-censored trades are excluded from tail diagnostics.

## Scientific interpretation guard

The word “idiosyncratic” in the family name does **not** mean a beta-residualized return. The frozen preregistration explicitly defines the shock as the asset's own standardized completed 1h return plus a BTC market-direction exclusion filter. Replacing it with a BTC residual now would change the hypothesis and is prohibited.

## Pre-execution risks to inspect if Phase223 becomes eligible

1. Sparse-event pathology at K=3.5: require meaningful trade counts per fold before interpreting PF/payoff.
2. Concentration: inspect additive asset PnL contribution and max absolute contribution share; no single-asset rescue.
3. Regime dependence: bull/bear/sideways diagnostics are descriptive robustness evidence, never a post-hoc regime selector.
4. Cost fragility: base -> severe -> supersevere return must be monotone; an edge that disappears at severe cost is not rescued.
5. Tail asymmetry: compare p01/p05 against p95/p99 and worst/best closed trade; do not infer quality from aggregate return alone.
6. Reproducibility: require byte-identical rerun and internal deterministic payload SHA before any decision.

No parameter, threshold, universe member, fold, cost, funding convention, or gate was changed by this audit. V16/V99 evidence is not used.