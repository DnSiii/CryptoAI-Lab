# V99 — ALL-REGIME STRUCTURAL REBUILD STANDARD

Status: RESEARCH ONLY. Frozen V16 and V99 Frozen are immutable benchmarks.

## Mission

V99 is no longer evaluated as a better V16 overlay. The research target is an all-regime engine that seeks maximum compounded profit while simultaneously improving trading quality, downside behavior, consistency, and regime robustness.

The comparison baseline is the metric-by-metric envelope of V13, V14, V15, and V16. If different engines own different best metrics, V99 is compared with each best value separately.

R64 is REJECTED under this standard. Strong ROI is insufficient when the candidate loses the benchmark envelope on drawdown, worst day, or broader quality dimensions.

## Immutable boundaries

- Do not modify frozen V16.
- Do not overwrite V99 Frozen or its paper history.
- New work lives only under `research/*`.
- Historical results never become forward/paper profit.
- No promotion from a single horizon, single cost model, or single regime.
- No post-hoc threshold changes after holdout is observed.

## Structural audit findings

### 1. Current Frozen V99 is not a standalone all-regime engine

Frozen V99 is a V16 core plus a consensus-gated persistent alpha satellite capped at 10%, rebalanced monthly. This is a valid frozen portfolio construction, but it is not the architecture now required for the new V99 mission.

### 2. Modern R98 research is still mostly a V15-derived hedge/risk/exposure router

R98 inherits a chain that routes between hedge amplitudes and selectively expands exposure. Its main source target stream remains V15-derived. This can improve a parent, but it does not by itself establish independent all-regime alpha.

### 3. Direction-blind/global risk reduction is structurally incompatible with the new objective

The original V99 risk stack takes the minimum of stress, chop, and damage multipliers and applies it to the transformed portfolio. Broad portfolio cuts can reduce a position that is correctly aligned with a crash or squeeze.

The R37/R55 lineage also creates a BTC hedge with direction `-sign(portfolio net)`. During a BTC crash, a net-short portfolio therefore receives a long BTC hedge even when the short book may be winning. This behavior must not survive into the rebuilt engine.

### 4. Risk control and alpha generation are currently too entangled

A regime or drawdown event may change exposure even when the underlying side is profitable. In the rebuild, alpha generation, regime routing, and risk control are separate layers with separate diagnostics.

### 5. The existing research gate is incomplete for the new mission

Existing gates emphasize return, drawdown, worst day, costs, and horizon robustness. They do not make trade win rate, winning-trade count, profit factor, average winner/loser, losing streaks, positive-day ratio, and per-regime performance first-class promotion requirements.

### 6. The repository already contains multiple economically distinct alpha families

Available causal building blocks include:

- directional/time-series trend;
- regime momentum;
- cross-sectional momentum/reversal;
- funding carry / funding pressure;
- breakout and impulse breakout;
- mean reversion for non-directional markets;
- V16 convex/fast/slow/trend capture components.

The rebuild should use these as independently measured sleeves rather than merely adding more filters to one parent target stream.

## New architecture target

### Layer A — Native alpha sleeves

Candidate sleeves must have independent P&L attribution before entering the final engine.

1. **Directional Trend Sleeve**
   - symmetric long/short logic;
   - intended for persistent bull and bear trends;
   - winning shorts in falling markets and winning longs in rising markets are never automatically reduced by a generic market-stress flag.

2. **Breakout / High-Volatility Sleeve**
   - intended for expansion and impulse regimes;
   - bounded failed entries, asymmetric winner capture;
   - evaluated separately under severe costs.

3. **Sideways / Relative-Value Sleeve**
   - cross-sectional reversal and/or mean reversion;
   - market-neutral or tightly net-controlled where possible;
   - must prove positive expectancy in sideways regimes instead of borrowing bull/bear beta.

4. **Carry / Positioning Sleeve**
   - funding carry or confirmed funding-pressure logic;
   - must prove that funding edge survives trend filters and modeled funding itself.

No sleeve is assumed useful because it exists. Each one must pass causal train/holdout and regime tests on its own.

### Layer B — Causal regime router

Directional state is evaluated as:

- BULL
- BEAR
- SIDEWAYS

Volatility state is evaluated independently as:

- HIGH_VOLATILITY
- LOW_VOLATILITY

The audit also reports the 3x2 interaction matrix. Regime labels use closed information only and never future returns.

The router allocates capital among sleeves; it does not redefine each sleeve's signal after seeing holdout.

### Layer C — Side-aware, P&L-aware risk controller

Risk decisions are evaluated separately for long and short books.

Required behavior:

- crash + losing/misaligned longs -> reduce/hedge the long side;
- crash + profitable/aligned shorts -> preserve, and only increase if alpha/risk budget independently authorizes it;
- squeeze/rally + losing/misaligned shorts -> reduce/hedge the short side;
- rally + profitable/aligned longs -> preserve;
- neutral/chop -> reduce only sleeves proven weak in that regime, not the entire portfolio by default.

Global deleveraging is reserved for portfolio-solvency/liquidity constraints, not used as the normal response to directional market movement.

### Layer D — Portfolio construction

- risk budgets are sleeve-aware and side-aware;
- gross cap is a hard constraint, not the alpha signal;
- no secondary sleeve is allowed to force a winning core out solely because of shared breaker state;
- correlation/overlap between sleeves is measured before capital is added;
- additive capital must earn its place after fees, funding, slippage proxies, and turnover.

### Layer E — Execution

- signal at close t executes no earlier than open t+1;
- fees and funding are modeled;
- severe and super-severe cost tests are mandatory;
- turnover and cost contribution are reported by sleeve;
- execution delay and timing perturbations remain adversarial tests, not tuning inputs.

## New metrics

### Global metrics

- ROI / terminal wealth;
- absolute profit on a fixed starting-capital baseline;
- CAGR;
- max drawdown;
- worst day;
- positive-day ratio and count;
- trade count;
- winning trades and losing trades;
- trade win rate;
- profit factor;
- average winning trade;
- average losing trade;
- payoff ratio;
- maximum consecutive losing trades;
- maximum consecutive negative days;
- turnover;
- fees and funding;
- rolling-window positive-rate and dispersion diagnostics.

### Regime metrics

For BULL, BEAR, SIDEWAYS, HIGH_VOLATILITY, LOW_VOLATILITY, and the 3x2 intersections:

- compounded regime ROI;
- active hours/days;
- positive-day ratio and count;
- max drawdown on the regime-only return path;
- worst regime day;
- trade count by entry regime;
- winners / losers;
- trade win rate;
- profit factor;
- average gain / average loss;
- maximum losing-trade streak;
- rolling stability diagnostics where sample size permits.

## Benchmark envelope

For every comparable metric the audit records the best value across V13/V14/V15/V16.

Higher-is-better examples:

- ROI;
- terminal/absolute profit;
- win rate;
- winning trades;
- positive-day ratio;
- profit factor;
- average gain;
- rolling positive-window rate.

Lower-is-better examples:

- absolute max drawdown;
- absolute worst day;
- absolute average loss;
- losing-trade streak;
- negative-day streak;
- rolling-return dispersion when return level is not being sacrificed.

Raw values and deltas to the envelope must always be shown. A composite score can never hide a failed raw metric.

## Promotion philosophy

The optimization priority remains maximum compounded profit. Risk quality is not optimized by simply shrinking exposure.

A promotion candidate should therefore seek **asymmetry**:

- substantially more terminal wealth;
- equal or better quality metrics where possible;
- no hidden dependence on one regime;
- no catastrophic metric regression masked by higher ROI.

A candidate is not rejected merely because one secondary metric is microscopically below the envelope, but any material regression must be explicitly shown and justified by a much larger improvement elsewhere. The final goal remains to dominate as many dimensions and regimes as possible, not to game a single scalar score.

## Anti-overfit protocol

1. Architecture and feature families are declared before holdout inspection.
2. Numeric thresholds are either structural/economic or fitted on train only.
3. Holdout cannot change the chosen threshold or sleeve definition.
4. Chronological folds and alternative horizons are mandatory.
5. Random calendar windows are deterministic and repeatable.
6. Severe/super-severe costs are mandatory.
7. Remove-best-day and remove-best-trade tests measure tail dependency.
8. Regime results require minimum sample disclosure; small samples cannot be presented as strong evidence.
9. Forward paper remains independent of backtest promotion.

## R105 purpose

R105 is **not** a new trading candidate. It is the baseline structural audit that measures:

- V13;
- V14;
- V15;
- frozen V16 benchmark;
- current R98 research parent;

under the new global + regime + trade-quality framework.

Its output becomes the specification for the first true all-regime rebuild. The rebuild begins only after R105 identifies which benchmark owns each dimension, which regimes are weak, and how much of R98's performance comes from beta/overlay behavior versus genuine trade quality.
