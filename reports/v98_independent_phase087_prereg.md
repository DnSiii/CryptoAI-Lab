# V98 Independent Phase087 — Intraday Range-Concentration Spread (PREREGISTRATION)

Status: FROZEN BEFORE ANY PHASE087 PNL INSPECTION.

## Independence
Phase086 closed `FAIL_DATA_NO_ALPHA`: all 16,440 funding-interval observations were exactly 8h, so no alpha was attempted. Phase087 moves to a different mechanism: temporal concentration of realized intraday price range. It does not rescue Phase085 volume concentration and does not use volume, funding-rate/interval, return direction, V99/V16, Phase083 outcomes or any future holdout.

## Hypothesis / frozen score
Information shocks can concentrate realized range into a small subset of hours. For each symbol and completed UTC day, compute each hour's nonnegative Parkinson range energy `r_h = log(high/low)^2`; daily temporal concentration is HHI of shares `sum((r_h/sum(r))^2)`. At 00:00 UTC day t use only t-1 completed day. Require >=20 finite positive/zero hourly range observations and positive daily range-energy sum. Rank five frozen symbols; long highest concentration +0.375, short lowest -0.375, gross 0.75. Deterministic `(score,symbol)` ties; flat if fewer than two scores or no score dispersion. Daily rebalance; positions persist.

## Training / execution
Training only through 2025-12-31 with existing chronological folds and unchanged V98 BASE/severe/supersevere costs and funding. No parameter search.

## Frozen gate
ALL: aggregate return >0; daily PF >1.05; max drawdown >=-35%; no ruin; each chronological fold return >0 and PF >1.00; severe return >0; supersevere return >0. Always report payoff, win rate, positive days, regimes, concentration/tails, asset contribution and reproducibility hashes.

Any failure => REJECT_NO_RESCUE. No sign flip, alternate range estimator, lookback, HHI variant, threshold, cadence, gross, symbols, regime/cost/funding rescue. PASS => freeze and separately preregister confirmation. Phase083 cannot ever be reused as untouched holdout; a final candidate requires a genuinely future untouched window.
