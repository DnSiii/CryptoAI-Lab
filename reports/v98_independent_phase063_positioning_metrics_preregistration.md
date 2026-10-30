# V98 Independent — Phase063 Derivatives Positioning Metrics Feasibility Preregistration

Status: PREREGISTERED BEFORE ANY ALPHA OR PNL.

## Scientific purpose
Test whether an exchange-native derivatives-positioning family is reproducibly obtainable across the full V98 training era before defining any trading rule. This is DATA FEASIBILITY ONLY. It must not calculate crypto returns, join price bars, choose a sign, threshold, lookback, weighting, regime, exposure, or inspect validation/final holdout.

This family is distinct from the closed spot↔perpetual basis/dislocation families: feasibility concerns positioning/account-flow state variables, not price basis, mark/index spread, funding selection, forced liquidations, options, macro, stablecoin liquidity or on-chain activity.

## Frozen source and schema
Source: Binance public data archive (data.binance.vision), USD-M futures daily `metrics` archives.

Fixed symbols:
- BTCUSDT
- ETHUSDT
- BNBUSDT
- XRPUSDT
- SOLUSDT

Fixed fields required from each archive:
- `sum_open_interest`
- `sum_open_interest_value`
- `count_toptrader_long_short_ratio`
- `sum_toptrader_long_short_ratio`
- `count_long_short_ratio`
- `sum_taker_long_short_vol_ratio`

No symbol dropping, field dropping, alternate provider, endpoint-class substitution, partial-era rescue, transformation search, sign choice, threshold or subset rescue after observation.

## Frozen training-era checks
For every fixed symbol, require the daily metrics archive to be downloadable and parseable on each fixed UTC date:
- 2023-03-15
- 2023-09-15
- 2024-03-15
- 2024-09-16
- 2025-03-17
- 2025-09-15

Each symbol/date archive must contain at least one row whose timestamp/date is not after the fixed check date, and all six frozen fields must have at least one finite numeric observation. This yields 30 symbol/date archive checks and 180 field-level finite checks. No future archive, interpolation, neighboring-date substitution or forward rescue is allowed.

## Decision rule
PASS_DATA_ONLY only if all 30 frozen symbol/date archives are available and all 180 required field checks are finite under the frozen schema. Otherwise FAIL_DATA_NO_ALPHA and close this exact family without source/date/symbol/field rescue.

## If PASS_DATA_ONLY
Exactly one subsequent Phase064 positioning mechanism may be preregistered BEFORE any crypto PnL is computed. Phase064 must freeze the economic transformation, causal lag, cadence, exposure and training gate before PnL; use training-only crypto data; realistic trading costs and funding; base/severe/supersevere stress; chronological 2023/2024/2025 folds; regimes; concentration/tails; max drawdown; Profit Factor; payoff; win rate; positive days; reproducibility and anti-overfit checks. Validation remains closed until every frozen training gate passes. Final holdout remains untouched until training and validation pass and a candidate is formally frozen.

## Isolation contract
Engine namespace: V98 Independent only. V99 evidence/state/workflows/reports and V16 Frozen are forbidden inputs. Failures from Phase053/055/059/061 and the Phase062 transport failure must not be used to choose Phase064 signs, windows, thresholds, weights, gross, regimes, symbols or rescue variants.