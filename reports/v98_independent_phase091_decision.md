# V98 Independent Phase091 — Decision

Status: **FAIL_DATA_NO_ALPHA / CLOSED / NO RESCUE**.

The preregistered cross-venue feasibility gate was executed on the V98-only branch using the independently selected Bybit V5 linear-perpetual hourly source. The workflow's V98 invariant tests passed before the probe.

The public endpoint returned HTTP 403 on four identical-source attempts for every fixed symbol (BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, XRPUSDT). Consequently observed coverage was 0/26,304 expected hourly timestamps for every symbol; the >=99% BTC/ETH gate, >=95% four-of-five gate, reacquirability/hash gate, and bounded-data gate could not pass.

This is an access/reproducibility failure, not economic evidence. **No alpha, direction, crypto return join, strategy PnL, threshold, lookback, spread transform, validation, or holdout was executed.** Phase083 was not used for selection. V16/V99 were not used.

Under the anti-rescue rule, Phase091 is closed. The failed Bybit source will not be replaced inside Phase091 after observing the failure. Any future work must be separately preregistered and must not reinterpret this transport failure as alpha evidence.

Current champion: **none**.
