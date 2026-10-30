# V98 Independent Phase1204 — AE causal breakout + conditional convexity portfolio (2026-10-23)

## Independent hypothesis, no post-result rescue
Phase1202 already reports a structural failure of AD at a crisis gap with strict causal risk; Phase1203 independently audits the immutable 180 cells. AE is **not AD patched**: it must use independent source code, new deterministic accounting, no AD online expert weights/posterior, no AC ordinal conviction, no imported rejected alpha, no external V14/V15/V99 details. No 2025/2026 data or historical AE PnL before full preregistered implementation and freeze. Clean-4 only.

**North star:** maximize long-horizon net compounded wealth/CAGR without arbitrary upside ceiling, conditional on robust solvency, causal execution, actual exit liquidity, severe cost/funding, diversification, drawdown/tails and reproducibility. A low-return cash-only strategy is not a passing champion.

## Seven-slot composition (architectural hypothesis AE-1)
1. **Growth Core:** causal long/short *breakout persistence* positions on completed 1h bars; a directional position only when price closes outside its prior 240h channel with causal 48h volatility normalization. Persist state until opposite channel/volatility regime; no forward bar highs, no isolated alpha grid.
2. **Opportunity Sleeve:** causal cross-asset synchronized breakout *acceleration*, measured as count of assets with fresh channel breaks over the prior 24h, enters for fixed 12h then decays; this is a complementary conditional growth convexity sleeve, not AD funding-surprise trades.
3. **Relative-Value Sleeve:** dollar-neutral *breakout breadth dispersion* hedge, long assets with persistent upward breaks and short assets with persistent downward breaks; zero if the directional dispersion is absent, with precommitted equal notional long/short normalization, no covariance inversion or AD RV source.
4. **Stress/Recovery Sleeve:** stateful convex exposure to **prior** actual NAV drawdown and market downside acceleration; hedge inventory must be financed and executed before the stress bar. Explicit recovery state after precommitted 48h recovery; no same-bar hindsight stops.
5. **Regime Router:** causal two-state hazard-based trend-persistence classifier on 240h aggregate channel occupancy, distinct from AD Bayesian online likelihood. Only completed observations can route next-open orders.
6. **Dynamic Allocator:** **capital-growth budget** via deterministic fractional Kelly-style forecast from prior 336h realized sleeve net contributions with shrinkage and turnover penalty, capped by predeclared survival envelope; no AD multiplicative virtual-wealth posterior or optimizing a risk metric as objective.
7. **Risk Governor:** risk-aware *two-step order feasibility*: preregister full candidate and explicit flatten-to-cash feasibility under 81 intrabar signed OHLC corners, 720h funding stress, 336h quote depth, realistic open gaps, fees/slippage, concentration/gross/net caps, and no assumed free exits. If carried inventory cannot be liquidated at next open, fail closed rather than claim survival. This is not an AD interpolation rescue: independently architect order lifecycle, pretrade unwind reserves and actual-cash accounting from scratch.

## Ordered scientific gates
A. Implement and test causal breakout source, persistence and future perturbation invariance with no PnL; then independent sleeve/router/allocator.
B. Add executable cash/inventory ledger and independent governor, adversarial 81-corner/gap/funding tests and explicit crisis carry tests.
C. Fresh four-OS vendor attestation and immutable static source hashes; complete seven-slot 90 benign + 90 crisis synthetic structural cells, including realistic causal risk inputs; no silent exceptions.
D. Freeze AE code, parameters and five paths before official 2023 and 2024 chronological 90-cell economic training; require positive robust net CAGR in both folds, severe/supersevere costs, sleeve marginal growth, trade PF/payoff/win/tails, concentration/drawdown and reproducibility.
E. Only after training pass and internal freeze, touch untouched separate 2025 validation; only after that may external V14/V15/V99 benchmark be read. Failed gates reject AE without rescue.

All files must remain V98 Independent namespaced on `research/v98-independent-zero`.
