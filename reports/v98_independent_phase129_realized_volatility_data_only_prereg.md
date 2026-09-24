# V98 Independent Phase129 — BTC realized-volatility DATA_ONLY preregistration

Status: PREREGISTERED BEFORE VALUES / ALPHA / PNL.

## Scientific family
Independent market-state family derived only from the already-frozen V98 training canonical BTCUSDT hourly series. This tests whether a causal realized-volatility state is technically available before any trading hypothesis is permitted.

## Isolation
- Training window only: 2023-01-01 through 2025-12-31 UTC.
- Validation: unopened / null.
- Final holdout: unopened / null.
- V16 and V99: forbidden.
- Phase083 selection information: forbidden.
- No parameter search, no rescue, no alpha, no correlation, no PnL.

## Frozen transform
- Input: BTCUSDT 1h close from V98 canonical training data.
- Hourly log return uses close[t]/close[t-1].
- Daily realized volatility is sqrt(sum(hourly_log_return^2)) for each UTC calendar day.
- A day is eligible only with >=23 finite hourly returns; no interpolation or fill.
- The DATA_ONLY report MUST NOT emit realized-volatility numeric values.

## Frozen integrity gates
PASS_DATA_ONLY requires all:
1. canonical BTCUSDT file exists after the existing V98 training-only reconstruction step;
2. no timestamp after 2025-12-31T23:59:59Z is consumed;
3. >=1000 eligible UTC days in 2023-2025;
4. finite eligible-day coverage >=95% of calendar days represented after the first return;
5. zero duplicate timestamps;
6. timestamps strictly increasing;
7. deterministic timestamp/date manifest hashes;
8. validation/final_holdout remain null and V16/V99/Phase083 remain unused.

Failure decision: FAIL_DATA_NO_ALPHA and close this exact gate without threshold/lookback rescue. PASS only authorizes a separately preregistered economic hypothesis.