# V98 Independent — Phase165 VIX>=30 failure audit

Date: 2026-09-27
Branch: research/v98-independent-zero
Scope: training evidence only; validation/final holdout remain closed.

## Frozen predecessor
Phase164 tested the preregistered hypothesis `VIXCLS >= 30 => short equal-weight crypto basket`, 1-day causal lag, target gross 0.30, hard cap 0.35, with no threshold/lookback/parameter search and no rescue.

## Independent failure-mechanism audit
- Phase164 decision: `REJECT_NO_RESCUE`.
- Aggregate training return: -2.556971%; PF 0.737029; payoff 0.737029; max drawdown -7.376596%; 10 positive vs 10 negative days.
- Stress remains negative: severe return -2.664397%, PF 0.726805; supersevere return -2.832781%, PF 0.711031.
- Chronological folds: 2023 inactive/0%; 2024 -0.007874%; 2025 -2.549298%. The loss is therefore not a single favorable fold failing a cost gate; economically useful performance is absent.
- Activation is sparse: only 13 of 774 VIX observations satisfy the frozen threshold (1.6796%). This creates a low-sample event strategy with evidence concentrated in a small set of episodes.
- Regime attribution is unfavorable where the thesis should help most: bear approximate return contribution -2.9494%; sideways +0.4876%; bull inactive. The risk-off short did not protect the bear regime.
- Tail/concentration evidence is fragile: worst day -2.7624%, best +2.9152%; all positive and negative contribution is concentrated in the respective top/bottom 10 active days. ETH is the only asset with positive aggregate contribution share; BTC/BNB/XRP/SOL contribute no positive aggregate share.
- Costs are not the root cause: base PF is already <1 and higher costs degrade it monotonically.

## Causal conclusion
The preregistered conventional VIX>=30 risk-off mapping is rejected as an independent V98 alpha hypothesis on training. Failure is primarily economic/directional under the tested contract, compounded by sparse activation and event concentration; it is not a transport, reproducibility, or cost-only failure.

## Anti-overfit decision
No sign flip, threshold sweep (20/25/35/etc.), lag sweep, asset cherry-pick, or regime rescue is allowed for Phase164. Any future volatility hypothesis must be scientifically distinct and preregistered before PnL inspection.

## Governance
- Champion: none.
- Validation: unopened for this hypothesis.
- Final holdout: unopened for this hypothesis.
- V16 Frozen/V99 Frozen/V99 research/paper state: untouched.
