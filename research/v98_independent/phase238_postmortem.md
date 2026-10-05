# V98 Independent Phase238 — post-mortem

Decision: **REJECT_FAMILY_NO_RESCUE**.

## Decision-grade evidence
- Workflow run 37327782323 completed successfully.
- Firewall/invariants passed: training data strictly <2026-01-01, funding PIT, `beta.shift(1)`, residual autocorrelation lagged through t-1, frozen 8-spec grid.
- Two independent evaluator invocations were byte-identical: SHA256 `cb2e034d3fb77016ca9e0a150c42616c894710ec91d0bda8a75d3f808949ba97`.
- Mechanical validator: all 8 preregistered specs failed the annual gate; no passing spec.

## Failure mechanism
Representative `idac_beta168_ac168_k1_h4` already fails before severe-cost stress. 2023 base return = -38.06%, max DD = -51.43%, PF = 0.941, positive days = 41.37%. 2024 base return = -53.26%, max DD = -62.51%, PF = 0.923. Thus rejection is not a marginal transaction-cost issue.

Regime evidence is broad rather than a single rescue candidate. In 2023 base: bear -9.60% (PF 0.917), bull -31.67% (PF 0.864), sideways +0.27% (PF 1.007). In 2024 base: bear -22.23% (PF 0.901), bull -28.65% (PF 0.920), sideways -15.77% (PF 0.946). No regime filter is authorized after observing these results.

Cost fragility is severe as expected for a high-turnover cross-sectional signal: representative 2023 turnover L1=497.5; return worsens from -38.06% base to -56.28% severe and -78.22% supersevere. Asset attribution is also uneven (2023 base ETH -39.93%, XRP -21.52%, while BNB +13.82%), but excluding losing assets post hoc would be rescue/cherry-picking and is prohibited.

## Scientific conclusion
Lagged idiosyncratic residual autocorrelation, in this frozen construction and universe, has no robust long/short edge across chronological folds. The family is closed without sign-flip, regime rescue, asset exclusion, or parameter rescue. Holdout 2026+ remains unopened.
