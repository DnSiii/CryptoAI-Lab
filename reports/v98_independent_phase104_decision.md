# V98 Independent Phase104 — decision

Status: **REJECT_NO_RESCUE**.

Phase104 tested a preregistered, causal network-activity regime from Coin Metrics `AdrActCnt` for BTC and ETH. The experiment is rejected on the frozen training gate: aggregate return -26.80%, daily PF 0.9655, max drawdown -62.89%; 2023 (-41.84%) and 2024 (-7.06%) were negative, while 2025 (+36.72%) did not establish temporal robustness. Severe (-37.35%, PF 0.9379) and supersevere (-51.03%, PF 0.8961) both failed.

Failure-mechanism audit: the effect is not merely a cost problem. Base performance is already negative, the two earlier chronological folds fail before stress escalation, and bull-regime return contribution is materially negative. BTC and ETH contributions have opposite signs, so the aggregate is also unstable across assets rather than a broad network-usage premium.

No rescue is permitted through sign flip, alternate lookback, threshold, gross, asset subset, regime mask, cadence, cost model, or combination with rejected mechanisms. Validation remains closed; no future holdout is opened. Phase083 remains permanently ineligible for selection. V16 and V99 remain excluded.

Next admissible step: a DATA_ONLY audit of a distinct on-chain observable, transaction count (`TxCnt`), because Phase057 established only sampled endpoint availability and never validated full 2023-2025 continuity or computed a TxCnt alpha. Phase105 must not compute price returns, correlations, alpha or PnL.
