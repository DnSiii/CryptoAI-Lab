# V98 Independent OK — permanent original economic rejection (2026-10-31)

**OK IS REJECTED PERMANENTLY. No post-result sign, threshold, window, gross, funding or sleeve rescue.** This is NOT a V98 champion, not an independently validated engine, and not paper/live eligible. Hypothesis and economic gates were preregistered at commit `44a58c497e73ee86e49a45d35a88a5232df16cc7`, before any OK PnL. Initial workflow run [41190032108](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41190032108) failed **before PnL** due to a cloned physical-runner import typo (`v98_next_pretrade_prokection`); corrected without changing economic hypothesis or signal parameters in commit `8ec668fe86f080402208d0aff93bc600acd6540c`. First complete physical and economic run: [41190083341](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41190083341). GitHub Actions FAILURE is intentional binding economic rejection, not physical failure.

**Scope and evidence:** authenticated Clean-4 2022-12 warmup to 2024-12 training, 18,288 1h bars, native 9,144 funding rates and conservative hourly worst-side mark envelope (NOT exact funding-event markPrice), OI 72,264 authenticated hourly asset observations and 888 quarantined. Strict 168h four-asset OI mask: 95/105 eligible, 10 ineligible; only OI-dependent Opportunity disabled when missing. XRP and 2025/2026+ excluded. All **30/30** signed physical cells completed without invariant failure; 105 weekly source and allocator decisions independently reconstructed (27 core), 17,543 hours of signed settlement reconciled, 127 net rebalance events, 0 quantity mismatches, independent arithmetic/tamper gate passed. Both settlement orders agreed economically.

**Original full-system training economics (carried-before-fill):**

| Cost tier | CAGR | Max DD | Turnover USD | 2023 | 2024 |
|---|---:|---:|---:|---:|---:|
| Base | +35.5903% | -31.9199% | 356,799.60 | +52.5110% | +20.5970% |
| Severe | +33.0561% | -32.9021% | 349,442.87 | +49.5282% | +18.4449% |
| Supersevere | +30.3881% | -33.9643% | 341,755.42 | +46.3910% | +16.1768% |

**Eight binding economic failures:** in base and severe, both funding settlement orders fail CAGR (>80% base, >60% severe) and Opportunity marginal log-growth (>0.02). No physical invariant failures. Full-system ablation log-growth marginal:

| Tier | Opportunity | Relative Value | Stress/Recovery |
|---|---:|---:|---:|
| Base | -0.001942 | +0.031104 | +0.051080 |
| Severe | -0.002632 | +0.025160 | +0.043623 |
| Supersevere | -0.003372 | +0.018780 | +0.035618 |

The Opportunity sleeve was activated only **one** weekly decision in each training year and reduced net growth after costs; it cannot be cosmetically rescued by post-result threshold relaxation. Relative Value and Stress show positive *within-OK* marginal contribution in base/severe, but this does not salvage the rejected full portfolio or make either sleeve a validated standalone engine. Core-only base CAGR +30.45%; the entire OK full portfolio remains well below the frozen growth objective. Annual 2024 growth is positive but insufficient.

**Next independent architecture, not an OK revision:** seek a genuinely different wealth-compounding mechanism with more persistent net alpha and positive marginal contribution across all three sleeves, preregistered before training. Do not import OJ/OK results as tuneable parameters. Exact funding settlement remains externally blocked by four authenticated Binance USD-M fundingRate exports with `markPrice`, 2,286 events each (9,144 total), raw transport attestation and SHA256; see `v98_exact_funding_official_evidence_handoff_20261031.md`. Conservative hourly mark bounds do not establish exact event prices. **2025 has already been exposed** and is not an untouched validation set; a genuinely untouched future holdout must remain sealed until an internally frozen candidate passes training. No V14/V15/V99 tuning or benchmarks, no V16/V99 Frozen, V99 paper or live changes.
