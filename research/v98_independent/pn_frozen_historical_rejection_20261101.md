# V98 PN — frozen full-history economic rejection (2026-11-01)

**Binding decision: REJECT_PN_TRAINING permanently.** PN was preregistered at commit `5984fe0973a2c0e0bb4d5c426486f5c41a0a200c` before PN implementation, before PN physical results, and before the independent audit. Full physical + independent audit: [workflow run 41318474891](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41318474891). Immutable in-repository receipts: `pn_full_training_frozen_result_20261101.json` and `pn_frozen_independent_receipt_audit_20261101.json`. Workflow final failure is the deliberate **economic** rejection gate, not a source/runtime/reconciliation failure.

## Physical exposed-history evidence (Dec-2022 warmup through Dec-2025)

30/30 physical cells feasible, 157 weekly decisions; 143 with all four assets' 168h causal OI, 14 with all OI-dependent sleeves forced to cash. 106,920 native OI asset-hours verified and 1,272 quarantined; 13,524 native funding events use conservative hourly mark envelopes, **not** unattested exact settlement marks. 2025 has been exposed by prior V98 research, not a pristine holdout.

| PN full portfolio, carried-before-fill, simulated | Base | Severe | Supersevere |
|---|---:|---:|---:|
| CAGR | +6.05% | +1.96% | **-2.27%** |
| Max drawdown | -38.24% | -41.51% | -44.84% |
| 2023 return | +18.05% | +13.24% | +8.29% |
| 2024 return | +21.21% | +16.58% | +11.77% |
| 2025 return | **-16.64%** | **-19.71%** | **-22.89%** |
| Turnover, initial USD10k | USD1,040,360 | USD981,429 | USD922,076 |

Base: 154 net fill events, 14 forced safety fills; fees USD416.14, slippage USD208.07, funding **-USD948.72**. 371/1,096 positive days; worst 1% daily mean **-6.09%**; hourly NAV-change PF 1.0074, hourly payoff 0.9733, hourly win rate 50.86% (**not trade-level metrics**). Peak single-asset gross concentration 100%. This is not proof of a durable profitable strategy.

## Independent audit and irrevocable economic rejection

Separate decision implementation: **0 mismatches** across 157 decisions and five books, maximum weight difference 6.94e-18. Cash accounting: **0 mismatches over 26,303 hours**; independent fees/slippage/funding: **0 mismatches**. Independent receipt audit: **60/60 arithmetic checks**, **24/24 binding economic failures reproduced**, **4/4 receipt tampering attempts rejected**.

Leave-one-out net log-growth marginals, carried-before-fill:
- Opportunity: **+0.07299 base**, **+0.05725 severe**; nevertheless 2025 annual marginal is negative beyond the preregistered tolerance.
- Relative Value: **-0.04854 base**, **-0.05206 severe**; fails contribution and 2023 annual marginal.
- Stress/Recovery: **-0.03721 base**, **-0.04048 severe**; fails contribution.

The full portfolio fails the precommitted base CAGR >80%, severe CAGR >60%, base turnover <=USD1m, severe positive-2025 requirement and module contribution gates. The 24 failures were independently rederived under both funding orders. **No post-result parameter, sign, threshold, cost, gross or sleeve rescue is permitted.** Positive standalone Opportunity evidence is not a passing seven-slot system and cannot be extracted as a retrospectively selected champion.

## Remaining delivery blockers and next genuinely distinct research

No V98 complete engine passed internal economic gates, so **no** V14/V15/V99 benchmark, prospective/holdout certification, paper or live authorization. The exact **13,524 Binance USD-M funding-event markPrice fields** remain externally unavailable after HTTP 451. Required evidence is an authorized exchange-origin raw API/export with event identity, markPrice, funding rate, URL, original HTTP headers/Date, retrieval UTC, raw bytes, per-page SHA256 and independently verified custody. See `v98_exact_funding_mark_authorized_handoff_20261101.md`; a vendor SHA or premium candle alone does not establish exact settlement mark.

Next architecture should test an **economically distinct return source** at the complete-portfolio level (not alter PN): e.g. an independently sourced and preregistered basis/term-structure mechanism if authentic historical data and executable legs can be obtained; otherwise investigate a different causal mechanism with the existing authenticated sources. Preserve clean chronology, source-first execution, both funding orders, cost stress and marginal accounting. Avoid repetitive rare-trigger overlays and exposure inflation without net economics. V16 Frozen, V99 Frozen/research/workflows/reports/paper, contaminated Phase083, 2026+ and untouched future holdout were not accessed or modified.

**Scope:** only `research/v98_independent/pn_*` and `.github/workflows/v98-independent-pn-oi-leverage-migration.yml` were created/changed.