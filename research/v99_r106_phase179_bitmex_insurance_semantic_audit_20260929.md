# V99 R106 — Phase179 BitMEX insurance-fund semantic audit

Date: 2026-09-29
Decision: **REJECT at DATA/SEMANTIC gate; no alpha/PnL inspected.**

## Evidence harvested

1. BitMEX first-party API documents `GET /api/v1/insurance` as Insurance Fund History with currency, timestamp filters, pagination (`count <= 500`, `start`) and ascending order when `reverse=false`.
2. BitMEX's 2020 first-party insurance-fund explanation states the published series is a **daily snapshot** and explicitly says the intraday minimum is more important than end-of-day balance. It documents large intraday increases and decreases caused by the liquidation engine realizing gains/losses.
3. BitMEX announced on 27 Sep 2023 — inside immutable TRAIN — that part of USDT and ETH Insurance Fund allocations would be reallocated beginning 28 Sep 2023 over several weeks, exchanging balances for USD held with banking partners. Thus observed currency-balance changes can be administrative allocation changes rather than liquidation stress.
4. A later first-party announcement (6 Feb 2024, outside TRAIN and not used to tune any signal) independently confirms that BitMEX can rebalance Insurance Fund assets. It is provenance/semantics evidence only, not market data and not used for selection.

## Failure mechanism

The preregistration required balance changes to be attributable to systemic loss absorption, or to have a contemporaneous first-party event taxonomy capable of separating administrative changes. The historical insurance table exposes balances/timestamps/currency but no causal reason code for each delta. The documented Sep-2023 reallocation therefore makes `delta(balance)` non-identifying.

Daily snapshots also hide the intraday trough that BitMEX itself says is the risk-relevant quantity. A daily delta can be positive even after severe intraday drawdown and recovery, so the proposed realization has both **confounding** and **temporal aggregation** failure.

## Decision

Fail closed. Do not rescue by:
- deleting Sep/Oct-2023;
- selecting XBt after seeing which currencies look clean;
- hand-labeling only announced reallocations;
- smoothing/threshold search;
- using PnL to decide whether confounding matters.

The Phase179 integrity tooling remains useful as a reusable data firewall, but passing it would not override this semantic rejection.

V16 Frozen, V99 Frozen and holdout remain untouched.
