# V98 Independent JV — pre-PnL preregistration: intrahour volume concentration and price impact (2026-10-28)

**Prospective independent seven-slot hypothesis; freeze before JV source calculation and any economic PnL.** JU terminally rejected for turnover; JV does not reuse JU passive-taker-absorption, JR's taker-shift/rebound, JS's BTC lag propagation, or JT's downside beta. No JU parameters, weights or observed performance are used to select JV. No V14/V15/V99 internals, 2025 validation, 2026+, old holdout, Frozen, paper, or real orders.

## Native market mechanism
Test whether **where quote volume occurs inside a completed hour** and its **signed price impact** distinguish persistent informed accumulation from episodic churn. Exact Binance USD-M 5m 100 monthly ZIP+SHA sidecars Dec2022..Dec2024, pinned official 1h Clean-4 and native funding; reuse independent month-level 5m/1h reconciliation quarantine from run 40668217706, including all-asset quarantine 2023-11 and 2024-10. All new features are from 12 **completed** 5m subbars of hour t, first tradable execution t+1 actual open, not intrabar lookahead:
- `volume_hhi=sum((quote_5m/sum_quote_hour)^2)` (0..1; higher is concentrated volume);
- `signed_volume_impulse=sum((quote_5m/sum_quote_hour)*log(close_5m/open_5m))`;
- `late_volume_share=sum(quote_5m[8:12])/sum_quote_hour`;
- `directional_efficiency=log(close_hour/open_hour)/max(sqrt(sum(log(close_5m/prev_close)^2)),.001)`.
All exact source archive SHA and 5m→1h reconciliation, no gap fill; if any invalid monthly source, all assets masked for month. Canonical float serialization to 10 significant digits, exact dual-OS source-byte audit before economic use.

## Immutable seven-slot portfolio
1. Growth Core: every 336h, top two 672h native-funding-net momentum / 336h downside semivol floored .001, 65/35 long.
2. Opportunity: long highest 72h mean positive `signed_volume_impulse * max(late_volume_share-1/3,0)` when positive; budget .16, else return to Core.
3. Relative Value: long 50% asset with highest 72h mean directional efficiency, short 50% asset with lowest (distinct, stable ranks); budget .12.
4. Stress/Recovery: always long the asset with minimum 72h mean volume HHI in STRESS (distributed liquidity); in RECOVERY long highest positive impulse; NORMAL long highest 72h mean `directional_efficiency - volume_hhi`; budget .14.
5. Regime Router: STRESS if 72h equal-weight funding-net log return <-.025 AND last 24h mean HHI exceeds last 168h mean HHI; RECOVERY if 24h equal-weight net return >.01 and prior 72h net <0; else NORMAL.
6. Dynamic Allocator: 336h epochs, Opportunity .16 if active, RV .12, Stress .14, Core remainder >=.58. All three optional sleeves disabled if any asset source invalid in preceding 168h. Core and Full-minus-sleeve independently finance removed budgets; no post-result edits.
7. Risk Governor: unchanged V98 GL order-invariant buffered shared collateral; prior-only risk/exit-capacity; signed native funding and actual next-hour open; base/severe/supersevere, both funding orders, 81-corner oracle. Gross NORMAL .90, STRESS .72, RECOVERY .85.

**Pre-PnL source gate:** 100 original authenticated 5m ZIPs, 1h reconciliation and exact dual-OS feature bytes, quarantine propagation, future-mutation causality, gross <=1, >=8 Full-minus-optional funded target L1>.025 epochs for each sleeve in 2023 and 2024. Failure freezes JV before PnL.

**Economic gate if source passes:** five USD10k separately funded books x 3 costs x 2 funding orders x 2 OS = 30 physical cells; independent original 60-receipt audit and all-hour 81-corner settlement. Full positive annual base/severe log growth 2023 and 2024, two-year CAGR >50% base and >30% severe, severe max DD <45%, turnover <=USD600k base/severe, all optional Full-minus-ablation combined log growth >+.02 base/severe and each year >=-.03. PF, payoff, win rate, positive days, CVaR, concentration, signed funding, turnover and reproducibility mandatory. No economic rescue. If training passes, freeze then separate chronological 2025 validation and untouched future holdout; external benchmark only after internal freeze. No live trading.
