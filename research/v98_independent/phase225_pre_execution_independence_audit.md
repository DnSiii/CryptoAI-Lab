# V98 Independent — Phase225 pre-execution independence audit

Status: **PRE-RESULT / NOT EXECUTED**
Holdout: **2026+ CLOSED**.

## Scope
Phase225 is frozen as abnormal-volume cross-sectional reversal: completed-bar `r6`, abnormal volume versus a preceding 168h median excluding the signal bar, cross-sectional median residual, contrarian entry at next hourly open, and 4h/8h holding. This audit is deliberately written before Phase225 execution and cannot use Phase224 results.

## Economic distinctness
The proposed mechanism is not realized-funding dislocation (Phase224): funding is neither the trigger nor ranking variable. It is also distinct from the idiosyncratic-volatility shock family recently closed in Phase223: Phase225 conditions on **abnormal traded volume plus cross-sectional return residual**, rather than realized-volatility residual magnitude. The hypothesized microstructure mechanism is temporary price pressure/liquidity demand after unusually high participation, followed by short-horizon reversal.

## Main falsification risks fixed before execution
1. **Volume nonstationarity:** secular growth/decline in exchange activity can distort raw volume. The frozen 168h local median ratio limits but does not eliminate this; no adaptive rescue is allowed.
2. **Cross-sectional common move leakage:** residualization against the contemporaneous five-asset median is causal only because all inputs end at t-1. No close(t) information may enter an open(t) decision.
3. **Sparse-tail selection:** V=3 and R=2.5% may produce few trades. The preregistered >=30 trades/year gate remains binding; sparse specs are not rescued.
4. **Concentration:** a single volatile asset can dominate apparent alpha. Asset contribution and the >70% concentration flag remain mandatory.
5. **Costs/tails:** contrarian entries after shocks may suffer adverse continuation and gap-like tails. 7/14/28 bp stresses, closed-trade tails, worst trade, max drawdown and regime diagnostics are mandatory.
6. **Funding:** realized funding must be PIT if charged. The validated V98 realized-funding snapshot may be reused only as accounting input; it cannot become a Phase225 feature.

## Causality invariants required in implementation
- volume(t-1) is compared with median volume from t-169..t-2; t-1 must be excluded from its own baseline;
- r6 ends at t-1;
- cross-sectional median is computed only from t-1-known r6 values;
- signal at t-1 enters at open(t);
- return accrual begins only after entry;
- no same-asset overlap; gross portfolio exposure <=1;
- 2026+ is rejected at data load.

## Decision
**PASS_FOR_IMPLEMENTATION_AFTER_PHASE224_DISPOSITION.** This is a scientifically distinct next family, but the preregistered sequencing rule remains: Phase225 must not execute while Phase224 is unresolved. No thresholds, horizons, assets, gates or costs may be changed based on Phase224 outcome.
