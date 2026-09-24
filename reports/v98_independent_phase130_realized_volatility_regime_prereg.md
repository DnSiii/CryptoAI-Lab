# V98 Independent — Phase130 BTC Realized-Volatility Regime preregistration

Status: PREREGISTERED AFTER Phase129 PASS_DATA_ONLY AND BEFORE ANY REALIZED-VOLATILITY VALUE/DISTRIBUTION/CRYPTO-JOIN/PNL INSPECTION.

## Scientific hypothesis
Elevated realized BTC volatility is an adverse state for a passive speculative-crypto basket after realistic trading frictions. Test one deliberately simple risk-permission hypothesis: hold the equal-weight crypto basket only when BTC daily realized volatility is not elevated relative to its own recent causal history; otherwise remain flat. This is a single prior-driven hypothesis, not a parameter search.

## Frozen information set and causality
Input is exactly the Phase129 BTCUSDT hourly canonical training-only series, restricted to 2023-01-01 through 2025-12-31. Phase129 must equal PASS_DATA_ONLY.

For each UTC calendar day t, compute daily realized volatility as sqrt(sum of squared hourly log returns within t), requiring at least 23 finite hourly returns. Compute the trailing 28 eligible-day median using realized-volatility observations through t. Define low/normal volatility when RV(t) <= that median and elevated volatility otherwise. The state becomes tradable only at 00:00 UTC on calendar day t+1 and remains fixed until the next activation. The first 27 eligible observations are flat.

The 28-day median is frozen ex ante as a robust approximately four-week baseline. The +1-day activation lag prevents use before the complete UTC day t is known. No intraday/same-day activation, interpolation, alternate estimator, annualization choice, smoothing, threshold/lookback search, lag search, or rescue is allowed.

## Frozen portfolio
Assets: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT. Gross cap 0.75, equal weight.

- low/normal volatility: long basket at total gross 0.75;
- elevated volatility: flat.

No short sleeve.

## Evaluation and costs
Training only; frozen chronological folds from config/v98_independent.json. Evaluate BASE, severe, supersevere through existing exact V98 engine with funding. Report total return, max drawdown, daily Profit Factor, payoff, win rate, positive days, worst day, regime metrics, tails, concentration, per-asset contribution proxy, maximum open gross, state counts, and always-long 0.75-gross context benchmark.

## Frozen training gates
All must pass:
- aggregate total return > 0;
- aggregate daily Profit Factor > 1.10;
- max drawdown >= -35%;
- worst day >= -12%;
- every frozen chronological fold: return > 0 and daily PF > 1.02;
- severe and supersevere: return > 0 and daily PF > 1.00;
- no single asset >45% absolute contribution proxy;
- top-10 absolute daily-return share <=60%;
- maximum open gross <=0.75;
- both low_normal and elevated states occur.

Any failure => REJECT_NO_RESCUE. No threshold/lag/gross/asset/window/estimator tuning after results.

## Isolation
Validation and final holdout remain untouched. Phase083 is not selection evidence. V16 and V99 are forbidden. No V99 workflow/report/state may be read for tuning or selection. No parameter search or rescue.