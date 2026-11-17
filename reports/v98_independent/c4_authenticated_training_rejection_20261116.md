# V98 Independent C4 — authenticated Clean-4 training decision (2026-11-16)

Scope: research/v98-independent-zero, V98-only. Evidence: GitHub Actions run 43981694177, commit 582c4a0c0b81a7acd72e610560dafb49324990d9, artifact 14283862992 (SHA256 64e34029d364706cd5b21df3a4a09cb670442ef77976e692671d3ea77786b3fa). Training only, no holdout access. Native price and funding manifest SHA256: 01e7bdeb8bcaf34ee898e322cf20f4479c0e25a9066b40f8cd2446286259f8a8 and f33094dfc065aa862a529d46f36e15f8a418ab085780214a0423488d2ff49622.

## Full C4 composed results (27,048 hourly observations)

| Cost | Final equity (USD from 10,000) | Max drawdown | Asset cap post-fill breaches | Gross cap post-fill breaches |
|---|---:|---:|---:|---:|
| 1x | 15,057.66 | 15.69% | 0 | 0 |
| 2x | 14,267.78 | 15.85% | 0 | 0 |
| 4x | 13,194.27 | 16.98% | 0 | 0 |

Pre-fill per-asset cap exceedances were 413/359/288 at 1x/2x/4x, while post-fill exceedances were zero; max post-fill single-asset weight 40%, max gross 65% (below 75% cap). This is an execution gate, not evidence of economic superiority.

## Leave-one-out marginal final equity (USD, full minus without slot)

| Sleeve | 1x | 2x | 4x |
|---|---:|---:|---:|
| Growth | +2,252.43 | +2,196.74 | +1,786.14 |
| Opportunity | +2,054.91 | +1,901.34 | +1,551.85 |
| Relative value | +2,590.30 | +2,219.80 | +1,880.81 |
| Stress/recovery | **-2,300.32** | **-820.94** | **-668.87** |

All 12 ablations executed. Stress/recovery fails positive marginal contribution at every cost level, even though the other three sleeves contribute positively. The version as composed is **REJECTED / NOT PROMOTED**. Do not remove the failed sleeve after seeing results and label the same candidate as a preregistered pass. Any replacement requires a genuinely distinct preregistered complete architecture, new chronological evaluation and separate validation.

## Additional ledger diagnostics (independent artifact calculation)

The artifact's 27,047 per-fill ledger rows show positive-day counts 456/446/432 out of 1,127 index-based 24-row groups for 1x/2x/4x, respectively. Approximate per-hour arithmetic gross-positive/gross-negative net-equity return ratio (not trade-level Profit Factor) 1.055/1.049/1.040. Four equal-length chronological segments of ledger equity show returns 1x: +0.85%, +55.33%, -6.40%, +2.70%; 2x: -0.14%, +48.95%, -4.42%, +0.36%; 4x: -2.08%, +42.92%, -5.40%, -0.33%. These segments are diagnostics, not independent validation folds. Ledger final equity is about USD 1 higher than summary in each cost scenario; reconcile the last observation/terminal execution before using ledger-based exact PnL claims.

## Next critical path

1. Keep C4 rejected and the old Phase083 holdout contaminated. Do not use 2026+ data for training or consult V14/V15/V99 before V98 internal freeze.
2. Preregister a genuinely distinct seven-slot architecture, with stress/recovery specifically designed for positive portfolio-level marginal growth rather than a cosmetic risk-only component.
3. Run full authenticated Clean-4 replay with 1x/2x/4x native costs, causal t-1 fills, chronological development/validation separation, per-sleeve ablations, regime/tail/turnover checks, and independently reconciled final equity; promote only after gates pass.

No live trading or independently validated CAGR is asserted.
