# V99 R106 — Phase183 rejection + Phase184 preregistration

Date: 2026-09-29

## Phase183 decision

Phase183 (ETH beta-adjusted residual dislocation mean reversion) is permanently rejected at TRAIN_ALPHA. No retuning is permitted.

Evidence frozen in `reports/candidate_v99_r106_phase183_train_alpha.json`:
- severe return: -41.1071%; max drawdown: -41.3723%; healthy folds: 0/5;
- supersevere return: -65.0363%; max drawdown: -65.1332%; healthy folds: 0/5;
- remove-best-hour remains strongly negative under both cost regimes;
- 975 active hours; all five chronological fold returns are negative under severe and supersevere;
- holdout market values parsed: false; V16 Frozen and V99 Frozen untouched.

Interpretation: the fixed mean-reversion sign is decisively unsupported. The failure is broad across time and costs rather than a single-tail accident. We will not invert Phase183 post hoc and call it the same experiment.

## Phase184 — preregistered hypothesis

### Hypothesis

A scientifically distinct hypothesis is that large beta-adjusted ETH residual dislocations exhibit **short-horizon continuation**, not mean reversion. This is motivated by the uniform Phase183 sign failure, but Phase184 is a new preregistered experiment and must not reuse Phase183 PnL to tune any magnitude, window, threshold, holding rule, or cost assumption.

### Frozen construction before Phase184 PnL

- Universe: BTCUSDT + ETHUSDT canonical hourly streams already admitted by the Phase182 pair-integrity gate.
- TRAIN only: observations strictly before `2024-01-18T00:00:00+00:00`; parser must stop before interpreting holdout OHLCV values.
- Economic start: `2021-12-01T00:00:00+00:00` after warm-up.
- Beta window: fixed 168 completed hours.
- At decision hour t, beta, residual location and residual scale use information available through t-1 only.
- Residual: `r_eth - beta * r_btc` on completed hourly returns.
- Standardization: fixed rolling 168h mean/std using completed residuals only; no expanding/forward imputation.
- Entry: `|z_{t-1}| >= 2.0` only.
- Direction: continuation — positive residual z => long ETH / short beta-adjusted BTC; negative residual z => short ETH / long beta-adjusted BTC.
- ETH gross leg: fixed 0.20; BTC hedge sized mechanically by the lagged beta, with no optimization.
- Position is recomputed causally each hour from the frozen rule; no discretionary exit/holding optimization.
- Costs: severe 0.0007 per side and supersevere 0.0014 per side, charged on turnover using the same accounting convention as Phase183.
- No threshold, beta window, z window, gross, sign, or cost sweep is allowed after observing Phase184 PnL.

### Mandatory TRAIN gates

1. Causality invariant: mutating contemporaneous/future prices cannot alter the signal at t.
2. Deterministic reproduction: two independent executions must be byte-identical.
3. Five chronological temporal folds; no shuffled CV.
4. Severe and supersevere results, max drawdown, active hours, fold returns, worst hour and remove-best-hour stress.
5. Tail/concentration audit: candidate cannot depend on one hour or one fold.
6. If TRAIN alpha is not positive and temporally credible under severe costs, permanently reject without retuning.
7. Only after TRAIN alpha passes may regime matrix + benchmark envelope be evaluated, still without holdout.
8. Holdout remains untouched until a formally frozen candidate passes every pre-holdout gate.

## Frozen assets

Do not modify V16 Frozen or `src/cryptoai_v13/v99_frozen.py`. Phase184 is research-only.