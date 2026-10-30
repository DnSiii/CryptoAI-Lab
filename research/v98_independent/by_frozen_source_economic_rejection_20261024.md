# V98 Independent BY — irrevocable source-level economic rejection (2026-10-24)

**Decision: REJECT_BY_SOURCE_MECHANISM_NO_RESCUE.** This is a source-level economic falsification of a directional native-funding-receipt + confirmed-price-dislocation mechanism, **not** a seven-slot system or system PnL. The immutable preregistration was committed at `03a98c84cacdb6ccc30937a57a6b98e05ad8be27` before any BY economic result. The final reproducible official run is **40099762173**, and the independently audited prior canonicalization run is **40099747150**. Both completed successfully and independently confirmed the same economic rejection on Ubuntu 22.04 and 24.04. No rescue, threshold change, sign change, cost change, holdout selection or portfolio CAGR claim.

## Exact source-only results, pinned original Clean4 2022-24
28 nonoverlapping 336h historical episodes, causal signal at completed close and next actual open execution, four Clean4 Binance USD-M contracts, native event funding and conservative marks. The numbers below are **sums of net per-entry-USD episode returns**, not investable annual returns or CAGR; no compounding, governor or fills were simulated.

| Entry year | Episodes | Sum of price returns per unit | Sum of native signed funding per unit | Severe roundtrip friction per unit | Severe net per unit |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2023 | 10 | +1.38386656 | +0.03164384 | 0.10471487 | **+1.31079553** |
| 2024 | 18 | +0.06681002 | +0.05447248 | 0.18620904 | **−0.06492654** |

2024 gross price + native funding = **+0.12128251**, less than severe roundtrip friction **0.18620904**. Thus the preregistered both-year severe-net gate fails. 2024 base episode-sum was **+0.08404070** and supersevere **−0.43734463**. In 2023 base **+1.39456743**, supersevere **+1.10136578**. The favorable 2023 does not rescue the negative 2024.

Causal prior-only median authorized notional **per selected episode** was about **USD35,409.89 (2023)** and **USD217,807.29 (2024)** under the existing physical capacity haircut; this is NOT proof of fills, available capital deployment or scalable PnL. Increasing 10m deployment requires independent historical order-book depth, queue/fill behavior and market-impact evidence; 1h quote volume alone cannot establish that.

## Independent replay and cross-OS numeric issue
The first official run **40099555534** failed exact cross-OS JSON equality; the original two source artifacts differed in exactly 13 last-bit diagnostic `past_336h_log_return` values (~1e-17), not in signal choices, price/funding cashflows, costs, capacity or annual results. This was forensically documented in `by_cross_os_float_transport_forensic_20261024.md`. The correction rounds **only the reported log diagnostic after raw-value signal selection** to 14 decimal places; raw decision thresholds, rank, native cashflow, costs and economic rejection remain unchanged. The independent auditor independently rederives that diagnostic, every signal, every native funding event, price, friction, capacity and annual result. Two subsequent official runs passed exact cross-OS receipt comparison and the independent replay.

## Decision and firewall
BY is permanently rejected at source-level. It must **not** be dressed up as a complete engine or tuned using its 2024 result. No 2025 future holdout, 2026+, XRP, contaminated Phase083, V14/V15/V99 internals or paper state was accessed. The V16/V99 Frozen state and V99 workflows remain untouched. No live orders or performance promises. **No V98 approved**. Next research must target a *genuinely distinct economic mechanism*, independently preregistered, with demonstrable severe-net edge and realistic capacity before another full seven-slot 90-cell investment; physical scaling beyond the existing prior-only limits remains an evidence constraint.

Evidence: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40099762173 ; https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40099747150 .
