# V98 Independent IR — permanently frozen historical training rejection (2026-10-27)

**Decision: REJECT_IR_HISTORICAL_MARGINAL.** IR native quote-price-impact resilience seven-slot portfolio is permanently rejected. No post-result modification of signs, windows, quote normalization, budgets, gross, clock, allocation or gates. It is **not** a complete V98 champion, is not independently future-validated, and is not authorized for paper or live trading.

## Immutable provenance and independent reproduction
- [Pre-code, pre-PnL IR preregistration](https://github.com/DnSiii/CryptoAI-Lab/commit/96c3e9930059e1f8fd1a830b29e7980cfb8f1a8a); [source, physical, OS and oracle implementation](https://github.com/DnSiii/CryptoAI-Lab/commit/fb0456d410a496d5f11cc7ae03fda5635c8fcaf6).
- [Canonical IR run 40553783290](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40553783290), pinned Clean-4 official artifact 40064588623, manifest SHA256 `833013a2e18836a203afd267ca698175907cff8f4c153c919a7811f14cb80752`. BTC/ETH/BNB/SOL USD-M 1h, Dec-2022 warmup, 2023–2024 training **only**. No 2025/2026+, XRP, Phase083, V14/V15/V99 internals, Frozen, paper or live.
- Pre-PnL source geometry, future-mutation causal test, zero-quote quarantine and signed financing PASS. Financed 14-day epochs 2023 Core/Opp/RV/Stress **27/27/27/27**; 2024 **26/24/24/24**.
- Five separately funded USD10k books x three native fee/slippage severities x two funding orders = **30/30 mechanically solvent configurations**; Ubuntu 22.04/24.04 both PASS. Independent original ZIP extraction (10 raw OS/book ZIPs) separately checked **60 raw cell receipts / 30 unique configurations**, all initial/final NAV, two-year CAGR, 2023-to-2024 continuity, signed funding/cost nonnegativity, OS numerical equality and source SHA: **zero errors**. The two funding orders do not represent independent market histories.
- Five independent all-settled-hour native oracle jobs PASS, **525,432 verified settlement-hour operations** and **65,646 funding-event-hour operations** across the five books. These are audit operations, **not trades or independent profitable samples**.
- GitHub Actions success indicates mechanically valid execution **not economic acceptance**. Artifact-only economic summary `ir30-official-economic-summary` returns `REJECT_IR_HISTORICAL_GROWTH_OR_MARGINAL` with errors [].

## Full IR 2023–2024 historical training only (USD10k)
| Metric | Base | Severe |
|---|---:|---:|
| 2023 net return | +61.06997% | +54.76489% |
| 2024 net return | +50.05252% | +46.77437% |
| Two-year CAGR | **+55.41677%** | **+50.67440%** |
| Max drawdown | 32.54326% | 32.76090% |
| Turnover USD | 216,637.59 | 205,732.06 |
| Signed native funding USD | -1,718.87 | -1,632.41 |
| Fees USD | 108.32 | 411.46 |
| Slippage USD | 108.32 | 617.20 |
| Hourly net profit factor | 1.04276 | 1.04022 |
| Hourly net payoff | 0.98251 | 0.98328 |
| Hourly net win rate | 51.4873% | 51.4069% |
| Positive UTC days | 368/731 | 366/731 |
| Worst 1% hourly CVaR | -1.5606% | -1.5511% |
| Peak single-asset gross concentration | 85.4616% | 85.4616% |

## Independently recomputed Full-minus-physical-ablation NET log growth
| Sleeve | Base 2023 | Base 2024 | Base total | Severe 2023 | Severe 2024 | Severe total | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| Opportunity | -0.029355 | -0.001120 | **-0.030475** | -0.040391 | -0.009354 | **-0.049745** | FAIL |
| Relative Value | -0.127013 | -0.016798 | **-0.143811** | -0.133285 | -0.022450 | **-0.155735** | FAIL |
| Stress/Recovery | -0.149383 | -0.063725 | **-0.213107** | -0.159459 | -0.071675 | **-0.231134** | FAIL |

All three optional sleeves have negative combined marginal net log growth, failing the precommitted >+0.02 combined gate. Growth annual positivity, base CAGR >50%, severe CAGR >30%, severe DD <45%, turnover <=USD600k, mechanical survival, reproducibility and independent settlement all pass; this **does not** rescue the three economic failures. IR's +55.42% is historical training CAGR, **not validated expected CAGR or realized trading PnL**.

## Structural first-fault attribution from the original physical books
The independently funded **Core-only** IR book returned **+69.99% historical training CAGR** versus **+55.42% Full**, and the minus-Stress book returned **+72.88%**. Full minus Core-only terminal NAV was **-USD4,748.77** on a USD10k starting book. Under base costs, Full minus minus-Stress terminal NAV was **-USD5,740.55**, despite the Full book having **USD441.95 less net funding expense** than the minus-Stress book; extra fee and slippage differences were only **USD24.56 each**. Thus the dominant failure is **directional opportunity cost and unfavorable sleeve financing**, not a missing fee discount or an untested synthetic unit. Cost-only tweaks cannot economically rescue this rejected architecture. These are training-only physical book comparisons, not future performance.

## Critical path
No complete V98 has passed internal economic gates. Future work must test a genuinely distinct, preregistered seven-slot economic mechanism (not IR price-impact score repackaged), prioritize positive financed portfolio-level marginal contributions and net compounding, and only after an internal complete freeze open separately preregistered chronological validation. Future holdout, external benchmarks, Frozen and paper remain untouched. No live trading authorization.
