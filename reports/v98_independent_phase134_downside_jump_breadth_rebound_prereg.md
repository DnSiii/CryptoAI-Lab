# V98 Independent — Phase134 Downside Jump Breadth Rebound preregistration

Status: PREREGISTERED AFTER Phase133 PASS_DATA_ONLY AND BEFORE ANY PHASE134 FEATURE VALUE/RETURN JOIN/ALPHA/PNL INSPECTION.

## Hypothesis
A broad, synchronous downside jump across the five V98 assets is a market-wide liquidity/overreaction shock. After a completed UTC day in which at least 3 of 5 assets register at least one sufficiently extreme negative hourly return, an equal-weight long basket during the following UTC day should earn positive net expectancy from short-horizon rebound.

## Frozen construction
Training only: 2023-01-01 through 2025-12-31 UTC; validation and final holdout forbidden. Assets: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT. For each asset/hour compute completed log return. For each asset/day define the scale using ONLY the preceding 28 completed UTC days: median absolute hourly log return. A downside jump occurs when hourly log return <= -3.0 times that prior scale. A broad shock day requires downside jumps in >=3 assets. Position activates only at 00:00 UTC on day t+1 and is held until the next 00:00 UTC decision. Broad-shock state: equal-weight long, total gross 0.75. Otherwise flat. No alternative direction, threshold, lookback, breadth, holding period, gross, asset exclusion or rescue search is allowed after PnL is observed.

## Frozen evaluation gates
Use the existing V98 exact backtest and funding treatment. Evaluate base, severe and supersevere costs/funding; chronological 2023/2024/2025 folds; regime metrics; concentration/tails; max drawdown; Profit Factor; payoff; win rate; positive days; reproducibility hashes; gross-cap invariant. PASS_TRAINING requires: aggregate return >0; daily PF >1.10; max DD >= -35%; worst day >= -12%; every yearly fold return >0 and PF >1.02; severe and supersevere return >0 and PF >1.00; single-asset absolute contribution <=45%; top-10 absolute-day share <=60%; max open gross <=0.75; at least 20 broad-shock activation days to avoid a tiny-sample promotion. Any failure => REJECT_NO_RESCUE.

## Isolation
V98 Independent only. No V16/V99 use; no Phase083 selection use; no parameter search; no rescue. Validation remains null unless all training gates pass. Final holdout remains untouched until a candidate is formally frozen after validation.