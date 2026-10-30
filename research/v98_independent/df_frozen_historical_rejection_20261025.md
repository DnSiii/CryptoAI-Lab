# V98 Independent DF — frozen historical rejection and independent native accounting review (2026-10-25)

**FINAL DF DECISION: REJECT_DF_HISTORICAL_GROWTH_OR_MARGINAL.** The complete DF seven-slot candidate is permanently rejected. No source, sign, pair, threshold, risk budget, leverage, fee or gross tuning to rescue DF; no cherry-picked sleeve promotion. The observation that one DF sleeve helped is not an approved standalone engine.

## Immutable chronology and evidence
- Pre-result seven-slot hypothesis: commit `65a5ce1fffe1558e0b9189f8d3ff8a7465c41fed`, before source `6208524992cecd2b465d6ab970cf783c370df3a7`.
- Source-only implementation and physical harness: `df_sources.py`, `df_source_viability.py`, `df_20cell.py`, `df_reconcile_20cell.py`, all DF namespaced.
- Corrected the 504h prior-volatility slice from 503h to 504h at commit `f21ca90807a3bc034676b5aa429eabb8f7655705` before examining either economic run. Original run `40166922950` is superseded, never used for selection.
- **Only authoritative DF economic run:** https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40166948692 (head `f21ca90807a3bc034676b5aa429eabb8f7655705`).
- Pinned Clean-4 training manifest digest `833013a2e18836a203afd267ca698175907cff8f4c153c919a7811f14cb80752`; BTC, ETH, BNB, SOL USD-M hourly, native funding, Dec-2022 warmup, 2023/2024 training. No XRP, 2025, 2026+, Phase083, external benchmarks, Frozen or paper.
- Source-only causal future perturbation PASS; effective epochs in 2023/2024 respectively: Growth 72/77, Opportunity 26/29, RV 21/33, Stress 23/25.
- **20/20 unique physical economic cells survived** (five paths x USD10k x base/severe x two funding orders), Ubuntu 22.04 and 24.04 reproduced; artifact-only official audit errors=[].
- Separate independent offline re-evaluation downloaded **all ten native per-path OS artifacts**, verified 40 per-OS physical cell receipts, NAV/return/CAGR identities, annual continuity, positive costs, holdout flags, both OS numeric reproducibility, and every annual marginal log-growth; **zero discrepancies**. This is an independent *artifact arithmetic* check, **not** event-by-event ledger replay.

## Complete-engine historical training, USD10k, carried-before-fill
| Metric | Base | Severe |
|---|---:|---:|
| Two-year CAGR | +69.6323% | +44.8633% |
| 2023 net return | +101.2867% | +73.8800% |
| 2024 net return | +43.0593% | +20.7500% |
| Max drawdown | 22.6033% | 31.0445% |
| Hourly net profit factor | 1.05408 | 1.03788 |
| Hourly net payoff | 0.99770 | 0.98968 |
| Hourly net win rate | 51.3741% | 51.1885% |
| Positive UTC day fraction | 43.2285% | 40.7661% |
| Peak gross/NAV | 0.76825 | 0.76401 |
| Peak single-asset gross concentration | **100%** | **100%** |
| Signed native funding | -$1,244.62 | -$992.53 |
| Fees + slippage | $1,372.58 | $5,576.36 |

## Independent annual full-minus-sleeve marginal net log-growth (USD10k)
| Sleeve | 2023 base carried | 2024 base carried | 2023 severe carried | 2024 severe carried | All 8 annual/cost/order cases |
|---|---:|---:|---:|---:|---|
| Opportunity | +0.030978 | **-0.008739** | +0.032676 | **-0.016325** | **6/8 positive — FAIL** |
| Relative Value | **-0.087753** | +0.048025 | **-0.094287** | +0.024360 | **4/8 positive — FAIL** |
| Stress/Recovery | +0.232160 | +0.065550 | +0.242041 | +0.034566 | 8/8 positive — PASS |

Core-only CAGR base +52.91%, severe +37.74%; full-minus-core final NAV +$5,399.38 base, +$2,014.64 severe. Full-minus-no-RV final NAV **-$1,167.03 base**, **-$1,520.75 severe**; RV marginal losses are dominated by 2023 price/portfolio interaction, not an isolated funding error. Full-minus-no-Stress final NAV +$7,414.47 base, +$5,073.63 severe. These are historical counterfactuals, not live PnL.

**Gates:** source PASS, physical survival PASS, cross-OS PASS, 2023/2024 positive net log growth PASS, CAGR thresholds PASS, severe drawdown PASS; **Opportunity and RV marginal gates FAIL**. Therefore DF **rejected** without opening sealed 2025 or testing external benchmarks. No supersevere/1m/10m or independent event replay was justified for this failed candidate. Peak 100% single-asset concentration remains an additional concern, not a reason to rescue DF.

**Next critical path:** preregister a *genuinely distinct* complete seven-slot economic mechanism whose Opportunity and Relative Value contribute net growth across chronological years and both funding orderings; avoid DF source/budget reuse and avoid post-result retuning. Independently replay native settlement events for any future candidate passing all training gates before declaring deliverable. V16/V99 Frozen and paper remain untouched; no real trading authorization.
