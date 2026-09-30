# V99 R106 — Phase185 rejection and Phase186 preregistration

## Phase185 decision

Phase185 (BTC shock -> ETH next-hour continuation) is permanently rejected at the TRAIN alpha gate. No retuning, sign flip, threshold search, window search, or holdout inspection is permitted.

Recorded TRAIN evidence (commit 284569da): severe return -14.8125%, max drawdown -16.8766%, 0/5 healthy temporal folds; supersevere return -33.4942%, max drawdown -34.1442%, 0/5 healthy folds. Remove-best-hour remains negative in both cost regimes. The failure is therefore distributed across temporal folds and survives tail removal; it is not justified to continue this family.

V16 Frozen and V99 Frozen remain immutable. Holdout market values remain untouched.

## Phase186 — volatility-shock conditional ETH/BTC relative continuation

### Scientific motivation

Phases182-185 rejected unconditional relative-stress/residual/lead-lag forms. Phase186 tests a distinct conditional mechanism: cross-asset relative continuation is allowed only after an objectively large BTC volatility shock, rather than after return direction alone. This is a regime-conditioned hypothesis, not a retrospective repair of Phase185.

### Preregistered construction

- Universe: canonical BTCUSDT and ETHUSDT hourly OHLCV already admitted by the Phase182 data gate.
- Research interval: TRAIN only; hard end-exclusive 2024-01-18T00:00:00Z.
- Information set: all predictors used for position at hour t must be computed from observations through t-1 only.
- BTC shock variable: absolute BTC close-to-close return at t-1 divided by trailing 168-hour realized volatility estimated strictly from returns ending at t-2.
- Trigger: standardized BTC shock >= 2.0. Threshold is frozen before PnL.
- Direction: sign of ETH-minus-BTC return at t-1; trade the same relative direction for hour t (relative continuation).
- Position: gross 0.20, split +0.10/-0.10 across ETH/BTC according to the relative signal; market-neutral gross exposure.
- No parameter sweep. Window=168h, threshold=2.0, horizon=1h and gross=0.20 are fixed.
- Warm-up observations are not imputed.

### Evaluation gates

1. Deterministic causal/invariant tests, including a contemporaneous-price mutation test.
2. Five chronological temporal folds on TRAIN only.
3. Severe and supersevere transaction-cost assumptions identical to the current V99 R106 discipline.
4. Tail/concentration audit including remove-best-hour and worst-hour.
5. Immediate permanent rejection if either cost regime has no credible fold breadth, materially negative aggregate return, or dependence on a single tail event.
6. Only if TRAIN alpha survives: freeze artifact first, then regime matrix and benchmark envelope. Holdout remains prohibited until those gates pass.

### Anti-overfit lock

After the first economic result is observed, do not change direction, window, threshold, horizon, gross, costs, fold boundaries, or trigger definition. A failure closes Phase186 permanently; any subsequent hypothesis must be scientifically distinct and separately preregistered.
