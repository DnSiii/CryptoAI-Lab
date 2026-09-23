# V98 Independent — Phase125 Policy-Uncertainty Regime preregistration

Status: PREREGISTERED AFTER Phase124 PASS_DATA_ONLY AND BEFORE ANY EPU VALUE/DISTRIBUTION/CRYPTO-JOIN/PNL INSPECTION.

## Scientific hypothesis
Elevated US economic-policy uncertainty is a risk-off condition for speculative crypto assets. Test a deliberately simple permission regime: hold the equal-weight crypto basket only when policy uncertainty is not elevated relative to its own recent history; otherwise remain flat. This is a single prior-driven hypothesis, not a parameter search.

## Frozen information set and causality
Source is exactly Phase124 FRED USEPUINDXD and training window 2023-01-01 through 2025-12-31. Phase124 must equal PASS_DATA_ONLY.

For observation date t, compute the trailing 28-calendar-observation median of USEPUINDXD using observations through t. Define low/normal uncertainty when value(t) <= that median and elevated uncertainty otherwise. The state becomes tradable only at 00:00 UTC on calendar day t+2 and remains fixed until the next activation. The first 27 observations are flat. No same-day use, interpolation, alternate source/release lag, smoothing, threshold/lookback search, quantile search, or rescue is allowed.

The 28-observation median is frozen ex ante as a robust approximately four-week baseline, chosen for interpretability rather than optimized performance.

## Frozen portfolio
Assets: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT. Gross cap 0.75, equal weight.

- low/normal uncertainty: long basket at total gross 0.75;
- elevated uncertainty: flat.

No short sleeve.

## Evaluation and costs
Training only; frozen chronological folds from config/v98_independent.json. Evaluate BASE, severe, supersevere through existing exact V98 engine. Report total return, max drawdown, daily Profit Factor, payoff, win rate, positive days, worst day, regime metrics, tails, concentration, per-asset contribution proxy, maximum open gross, state counts, and always-long 0.75-gross context benchmark.

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

Any failure => REJECT_NO_RESCUE. No threshold/lag/gross/asset/window tuning after results.

## Isolation
Validation and final holdout remain untouched. Phase083 is not selection evidence. V16 and V99 are forbidden. No V99 workflow/report/state may be read for tuning or selection. No parameter search or rescue.
