# V98 Independent OW — FROZEN REJECTION (2026-10-31)

**Binding: REJECT_OW_TRAINING. No V98 champion.** The pre-registered seven-slot directional path-efficiency / residual-dispersion architecture failed its economic gates. Do not change OW signs, windows, thresholds, weights, gross caps, costs, funding ordering, or gates after this result. OW cannot be cosmetically rescued or re-promoted. No 2026+, XRP, contaminated Phase083 holdout, V14/V15/V99 signals or benchmark internals, V16/V99 Frozen, or paper/live state accessed or changed.

## Original evidence and provenance
- Pre-result preregistration commit: `95aad8c5bd57f76b61dd9490c4da55f72f6ed073`.
- Physical engine + independent signal oracle run: [GitHub Actions 41245178372](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41245178372), pinned head `7354065288d4bbecab710051eada8fd9d9d0382c`. Run is marked failure **intentionally because the economic gates rejected OW**, not because 30-cell settlement crashed.
- Original result archived in `ow_full_training_frozen_result_20261031.json`, with original Actions artifact ID `13058542416`.
- Separate post-freeze independent arithmetic/cost/gate verification: [GitHub Actions 41245327256](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41245327256), **PASS_INDEPENDENT_OW_FROZEN_REJECTION_AUDIT_NOT_ENGINE**.

## Original modeled economics (OW_full, carried-before-fill, initial USD10,000)
| Tier | CAGR | Max drawdown | Turnover USD | Final equity USD | Funding cash USD |
|---|---:|---:|---:|---:|---:|
| Base (4+2bps) | **-3.1034%** | -46.0805% | 989,429.79 | 9,097.39 | -735.17 |
| Severe (10+10bps) | **-8.2659%** | -48.0405% | 910,641.40 | 7,719.09 | -694.54 |
| Supersevere (15+20bps) | **-13.5058%** | -50.1685% | 835,082.35 | 6,470.21 | -654.96 |

Base annual modeled returns: 2023 -13.1715%, 2024 -0.5357%, 2025 +5.3384%. Severe annual: 2023 -18.0942%, 2024 -5.9268%, 2025 +0.1811%. Base 477/1096 positive days. Base hourly NAV-increment PF 0.9962 (NOT trade PF). All figures are exposed exploratory historical modeling with native rates and conservative hourly mark envelopes, **not** exact event-mark settlement, untouched validation, prospective returns, or paper/live PnL.

## Full-system audit
- All **30/30** physical cells settled: five books × three cost tiers × two funding orderings. No physical insolvency gate failed.
- Independent source-causal signal and allocator oracle: **157 decisions × five books**, zero mismatches.
- Independent hourly cash identity: **26,303 hours**, zero mismatches; max cash error ~1.82e-12 USD.
- Independent net-fill/fee/slippage/funding oracle: **202 net fill events**, **3,287 funding hours**, zero mismatches.
- Independent frozen receipt audit: **120** cost/growth arithmetic checks, all 30 unique cells, all **24** economic failures rederived; maximum arithmetic discrepancy ~1.82e-12 USD.
- Base full-minus-ablation log growth: Opportunity **+0.000726** (<+0.02 gate), Relative Value **-0.027064** (negative), Stress/Recovery **+0.001055** (<+0.02). Severe: Opportunity +0.000870, RV -0.046772, Stress +0.000960. Full portfolio underperformed its core-only ablation (base CAGR -3.103% vs -2.088%). No standalone module rescue.
- **24 binding economic failures** across both funding orders: base/severe CAGR, severe drawdown, negative severe calendar years, all three optional sleeve marginal gates and RV's 2025 annual marginal. OW is definitively rejected.

## Delivery status and non-cosmetic next step
The decisive bottleneck is **not a missing unit test or 30-cell workflow**: the composed portfolio loses money after costs and its RV sleeve is materially destructive. Further cosmetic tuning of OW is prohibited. The next independent architecture must use a *genuinely different economic return mechanism* and be preregistered before any PnL; focus on growth/compounding with genuine positive full-system marginal contribution, not just lower risk. The seven-slot architecture and immutable cost/causal/holdout gates remain binding.

**Independent external source blocker:** 13,524 exact Binance USD-M `/fapi/v1/fundingRate` original event objects containing `markPrice` for BTC/ETH/BNB/SOL, Dec-2022–Dec-2025, plus raw HTTP page bodies, SHA256, request/response metadata and independent exchange-origin transport attestation. This is **9,144** events for 2022–24 and **4,380** for 2025. Existing GitHub runner egress has returned HTTP451/202/400/timeouts. Alternative: an authorized exchange-origin export with verifiable chain of custody and the existing V98 importer/auditor; synthetic fixtures and Binance Vision funding-rate-only ZIPs cannot prove exact settlement marks. A future **untouched prospective validation and final holdout** are also required after an internally passing candidate. 2025 is already exposed and cannot be called virgin validation. No operation real or paper authorized.
