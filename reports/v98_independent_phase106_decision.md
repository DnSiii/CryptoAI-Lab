# V98 Independent Phase106 — decision

Status: **REJECT_NO_RESCUE**.

Phase106 tested a preregistered BTC-vs-ETH rotation using 28-day log growth in Coin Metrics `TxCnt`, with strict D-1 information, daily rebalance, equal long/short weights and 0.75 gross. It failed decisively: aggregate return -34.01%, daily PF 0.8718, max drawdown -38.39%; all three chronological folds were negative (2023 -13.76%, 2024 -11.62%, 2025 -13.41%). Severe (-50.41%, PF 0.7886) and supersevere (-68.45%, PF 0.6760) also failed.

Failure audit: the result is not a single-regime or cost-only pathology. Bear, bull and sideways return contributions are all negative, both early and recent folds fail, and the stress deterioration is monotonic. Asset contribution is balanced enough to rule out a one-symbol fluke. Therefore there is no scientific basis for sign flip, alternate horizon, threshold, cadence, gross, subset, regime mask or other rescue.

Validation remains closed. Phase083 and opened/future holdout data remain ineligible for selection. V16 and V99 remain excluded.

Next admissible work must introduce a materially different on-chain observable. Phase107 is restricted to DATA_ONLY feasibility of adjusted transfer value in USD (`TxTfrValAdjUSD`), representing economic value moved rather than participant or transaction counts. No alpha/PnL is authorized by this decision.
