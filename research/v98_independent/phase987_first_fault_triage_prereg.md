# V98 Independent Phase987 — first-fault source attribution (preregistered)

Scope fixed to Binance USD-M BTCUSDT 1h **2023-02** only (672 UTC hours), before any historical PnL. Phase959's mark chronology/geometry rejection and Phase962's first failing month are immutable prior evidence. Clean-4 remains BTC/ETH/BNB/SOL; XRP remains quarantined.

Protocol, before inspecting outcomes:
1. Fetch monthly mark ZIP and corresponding vendor CHECKSUM from the fixed Binance archive; verify SHA256, preserve the original bytes, and run the original Phase797 strict parser **unchanged**.
2. Independently inspect all 672 monthly rows, classify the **first** anomaly by UTC hour (OHLC geometry, close time, row count, timestamp, or ZIP member).
3. Fetch **only the matching UTC day** from the Binance official daily mark ZIP and CHECKSUM; compare the exact first-fault UTC timestamp without positional substitution or interpolation. Independently query the Binance markPriceKlines API for a bounded nearby observation when the source row is present.
4. Persist all results, including incomplete transport or contradictory evidence. Any anomaly, missing evidence, or source disagreement remains quarantined; even agreement never authorizes PnL or a changed source gate.

The diagnostic is intentionally narrow: it locates and attributes the first fault quickly before considering a separate complete 28-day reconciliation. The old Phase083 holdout, 2025 validation, 2026+ data, external V14/V15/V99 benchmarks, frozen N parameters, and all non-V98 files are out of scope. No post-result rule changes or market-price corrections.