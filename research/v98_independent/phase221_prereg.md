# V98 Independent Phase221 preregistration — BTC-beta residual cross-sectional continuation

Preregistered after Phase220 decision-grade rejection and before any Phase221 result is observed.

## Scientific hypothesis

Test a price-only, funding-independent mechanism distinct from Phase219/220: after removing each altcoin's trailing causal BTC beta, unusually strong/weak idiosyncratic return may persist briefly. This is **not** a rescue or sign inversion of funding dispersion. No Phase220 winning asset/regime/tail observation is used to choose the signal.

## Frozen universe and firewall

Universe: ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT; BTCUSDT is benchmark only. Canonical hourly prices only. All feature inputs and rolling estimates at decision hour `t` must end at `t-1`; use `pct_change(fill_method=None)`. No timestamp >= 2026-01-01 may be loaded into research/evaluation. 2026+ remains untouched holdout.

## Frozen feature

For each altcoin i and hour t:

1. Compute hourly log/simple return consistently from canonical close.
2. Estimate rolling beta to BTC using only returns through t-1: `beta_i = cov(r_i,r_btc)/var(r_btc)` over W hours, with full-window requirement.
3. Residual hourly return: `eps_i = r_i - beta_i*r_btc`.
4. Residual continuation score is the sum of residual returns over the last L completed hours, ending t-1.
5. Cross-sectionally rank the four altcoins at t. Long highest score +0.5, short lowest score -0.5. No position if required inputs are missing/tied/non-finite. Gross exposure <=1.

Exactly 8 frozen specs: `W in {168,336} x L in {6,24} x hold in {4,8}`. No threshold, asset, side, regime, or parameter changes after results.

## Execution and costs

Positions are entered only after signal information is available; non-overlap per asset/strategy must be enforced deterministically. Apply the repository's established V98 realistic trading-cost convention plus the same severe and supersevere multipliers used by adjacent V98 phases. Funding must be charged PIT for any funding timestamps actually crossed by each held perpetual position; funding is a cost/carry term only, never a Phase221 feature.

## Required evaluation

Chronological folds: 2023, 2024, 2025 separately. For every spec/fold/stress report return, max drawdown, Profit Factor, payoff, win rate, positive days, trades, p01/p05/p50/p95/p99, worst/best trade, max asset concentration, funding contribution, and bull/bear/sideways attribution.

Run deterministically twice and require byte-identical result SHA. Assert timestamp ordering/no duplicates, `t-1` causality, full rolling windows, finite beta denominator, gross exposure <=1, non-overlap, and monotonic degradation from base -> severe -> supersevere costs.

## Mechanical gate

A spec is training-fold coherent only if **base return > 0 and base Profit Factor > 1 in each of 2023, 2024 and 2025**. If 0/8 pass, reject the entire family without rescue. If one or more pass, do not open holdout automatically: first perform the already-required stress, concentration/tail, regime, causality/data-integrity and reproducibility audits. Any later holdout opening requires a separately documented pre-holdout promotion decision based solely on training evidence.

## Anti-overfit declaration

No V99 artifact, state, parameter, result, workflow, or paper information may be used. Phase220's asset/regime pockets cannot select Phase221 assets or directions. No post-result sign flip, subset selection, regime filter, parameter interpolation, or cost weakening is permitted. Champion remains unchanged until all gates are satisfied.
