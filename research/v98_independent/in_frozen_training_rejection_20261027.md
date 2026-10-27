# V98 Independent IN — permanently frozen historical training rejection (2026-10-27)

**Decision: REJECT_IN_HISTORICAL_GROWTH_OR_MARGINAL.** IN is not the V98 champion, not validated out of sample, and not authorized for trading. Do not cosmetically rescue IN by modifying sign, window, threshold, weights, gross, costs, funding, financing, turnover, source or execution after results. Rejected variants remain rejected.

## Immutable preregistration and provenance
- Preregistered **before IN implementation and IN PnL**: commit [18d385b](https://github.com/DnSiii/CryptoAI-Lab/commit/18d385bcd8874170909f2f9ad3b55856339fcd13).
- Original [GitHub Actions IN run 40524927032](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40524927032), pinned native Clean-4 2022–2024 artifact from run 40064588623. Source manifest SHA256 `833013a2e18836a203afd267ca698175907cff8f4c153c919a7811f14cb80752`.
- Only BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT, Dec-2022 warmup and 2023–2024 training. Causal completed close t and next actual open t+1, signed native funding/mark, independent USD10k physical cash books, no synthetic fills.
- Pre-PnL source/quote/causal-future-mutation checks PASS. Financed source epochs 2023 core/opportunity/RV/stress **53/41/52/50**, 2024 **52/40/50/39**.
- Artifact-label note: the first IN run used legacy `im-source-viability` and `im-independent-ledger-IN_*` ZIP **labels** inherited from the workflow template; payloads, jobs, paths and economic results are IN-only. The workflow artifact names were corrected in commit `9beccb3` after the first run started. No redundant economic rerun was performed.\n- **30/30** distinct physical book x cost x funding-order economic cells survive; Ubuntu 22.04 and 24.04 receipts reproducible; audit errors []. Five independent every-settled-hour native oracle jobs PASS: 105,258 settled-hour verifications and 13,152 funding-event-hour verifications per book; totals 526,290/65,760 are verification operations, **not** distinct trades or outcomes.
- Independently re-extracted all five original Ubuntu 22.04 book artifacts (30 physical cells) and original economic summary, recomputed all annual NAV/log-growth identities, cross-book source SHA and all 36 year x scenario x sleeve marginal differences **exactly** without rerunning economic decisions or changing parameters. Original artifacts are the source of truth.

## Full IN historical training, USD10k
| Metric | Base | Severe |
|---|---:|---:|
| 2023 net return | +71.3595% | +55.9767% |
| 2024 net return | +32.3110% | +19.6356% |
| Two-year CAGR | **+50.5326%** | **+36.5738%** |
| Maximum drawdown | 31.4000% | 34.7842% |
| Turnover USD | **814,821.84 (FAIL >600k)** | **719,660.43 (FAIL >600k)** |
| Native signed funding USD | -1,560.48 | -1,368.60 |
| Fees USD | 407.41 | 1,439.32 |
| Slippage USD | 407.41 | 2,158.98 |
| Hourly net Profit Factor | 1.04016 | 1.03081 |
| Hourly net payoff | 0.99515 | 0.99161 |
| Hourly net win rate | 51.1059% | 50.9691% |
| Positive UTC days | 372/731 | 365/731 |
| Worst 1% hourly CVaR | -1.4890% | -1.4786% |
| Peak single-asset gross concentration | 82.4788% | 82.4788% |

## Original full-minus-physical-ablation marginal NET log growth
| Sleeve | Base 2023 | Base 2024 | Base combined | Severe 2023 | Severe 2024 | Severe combined | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| Opportunity | +0.114943 | -0.019046 | **+0.095897** | +0.100556 | **-0.045753** | +0.054804 | FAIL annual severe < -0.03 |
| Relative Value | -0.040087 | -0.023725 | **-0.063812** | -0.067010 | -0.058667 | **-0.125677** | FAIL combined and annual |
| Stress/Recovery | -0.228298 | -0.069980 | **-0.298278** | -0.273912 | -0.115567 | **-0.389479** | FAIL combined and annual |

Both funding order conventions reproduce these values. Growth/CAGR and severe drawdown gates passed, but **turnover fails** and **all three optional modules fail the preregistered robust marginal gate**. Opportunity's positive two-year base marginal is not sufficient to rescue its failed severe 2024 annual result. Supersevere marginals deteriorate further. A profitable 2023–2024 full portfolio is not a validated full V98 engine and is not evidence of 2025/2026 performance.

## Decision and critical path
Freeze IN rejected. Do not tune it post-result. Next architecture must target persistent **net** growth above a strong independently funded core with materially lower structural turnover, avoiding ineffective relative-value and stress sleeves. A genuinely distinct economic hypothesis must be preregistered before data/PnL. Holdout 2025 sealed; no 2026+; XRP quarantined; Phase083 ineligible; V14/V15/V99 external benchmark internals unopened; V16/V99 Frozen, V99 research/paper and all live state unchanged. No trading authorization.
