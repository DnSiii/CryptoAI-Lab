# V98 Independent — Phase207 preregistration

Status: **FROZEN BEFORE RESULTS**

## Hypothesis
Cross-sectional residual momentum after removing the contemporaneous BTC market move may contain a more independent crypto-specific continuation signal than absolute momentum or BTC lead/lag. At each decision time, rank ETH/BNB/XRP/SOL by lagged residual return relative to BTC and trade only the strongest/weakest residual tails in the direction of the residual.

This is scientifically distinct from Phase205 BTC→alt propagation and Phase206 funding dislocation: the explanatory variable is each alt's own lagged return net of its rolling lagged beta to BTC, not BTC shock magnitude or funding.

## Frozen design
- Universe: ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT; BTCUSDT is benchmark only.
- All predictors strictly available at t-1 or earlier.
- Rolling beta estimated only from historical hourly returns ending at t-1; no centered windows.
- Residual lookback: {24h, 72h}.
- Beta estimation lookback: {30d, 90d}.
- Holding horizon: {8h, 24h}.
- Exactly 8 specs = 2 × 2 × 2; no post-result threshold additions.
- At each eligible decision, residual = alt cumulative lagged return minus lagged beta × BTC cumulative lagged return. Long the largest positive residual and short the most negative residual only when their signs agree with the trade; otherwise remain flat on that side. Equal notional long/short when both sides exist; single-side exposure allowed only when exactly one signed extreme exists.
- No asset exclusions or regime gates after results.

## Evaluation discipline
- Chronological training folds: 2023, 2024, 2025, independently reported.
- Validation/final holdout remain unopened unless a frozen candidate clears training gates.
- Realistic funding debits/credits using the already frozen Phase206 PIT funding snapshot where applicable; no future funding knowledge.
- Base, severe, supersevere trading-cost stresses reported independently; stress cannot rescue a failed base fold.
- Report return, max drawdown, Profit Factor, payoff, win rate, positive days, trade count, regime decomposition, complete-trade tails and concentration.
- Reproducibility: deterministic payload and repeated-run SHA256 equality.

## Mechanical family gate
A spec is training-stable only if all three base folds have return > 0 and PF > 1. Severe/supersevere, MDD, tails, concentration and regimes then act as robustness diagnostics/gates, never as post-hoc selection rescue.

If 0/8 specs are training-stable, reject the family with no inversion, asset cherry-pick, regime rescue, or parameter expansion.
