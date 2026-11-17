# V98 C9 authenticated sleeve ablation disposition — 2026-11-17

Scope: training-only Clean-4 (BTC, ETH, BNB, SOL), Binance USD-M 1h, native funding, 2022-12 warmup through 2025-12. No 2026+ or old Phase083 holdout. Independent V14/V15/V99 benchmarks not opened.

Evidence: GitHub Actions run 44129610694, commit 6f152c69d4963d08e864a982926f57e322785d9e, job 134202720194, artifact 14350556259, success at 2026-11-17T17:00:03Z. Baseline authenticated replay run 44107270718.

Final equity from $10,000: 1x $22,677.661117; 2x $17,659.418889; 4x $13,717.530188.

Leave-one-out marginal final equity (full minus without), USD:

| Sleeve | 1x | 2x | 4x |
| --- | ---: | ---: | ---: |
| Growth Core | +7751.69 | +3155.85 | +23.32 |
| Opportunity | +2253.75 | +1136.12 | +53.82 |
| Relative Value | +2795.78 | +2507.41 | +1149.81 |
| Stress/Recovery | +4744.27 | +1519.36 | +277.61 |

The preregistered four-sleeve training gate passes all 12 comparisons, **not a promotion**. At 4x the Growth and Opportunity margins are only 0.17% and 0.39% of full final equity, respectively; positive does not imply robust after uncertainty or separate chronological validation. Marginal equity is not additive across sleeves because allocation, compounding and costs interact. The other three system slots (Regime Router, Dynamic Allocator, Risk Governor) were not independently ablated by this workflow.

Decision: retain C9 as the current internally eligible **training candidate only**, not frozen champion, not paper-ready and not live. Do not retune using these results. Next critical gate: predeclare chronological training/validation split and pass separate unseen validation with complete portfolio, native costs/funding, tail and regime diagnostics, causality and reproducibility. Independently test router/allocator/governor contributions and survival constraints. Holdout remains untouched until candidate freeze and validation gates. Only then compare external engines.

No evidence of live or forward profitability; no new PnL inferred.
