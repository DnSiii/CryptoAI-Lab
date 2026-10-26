# V98 ER — immutable 2023/24 economic attribution (2026-10-25)

**PERMANENTLY REJECTED.** Official preregistered native 30-cell run https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40251198738 . Independent frozen-receipt-only attribution (no OHLC, no signals, no PnL replay, no 2025) https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40251440883 .

At USD10k, 2023/24 training, carried-before-fill: full CAGR +84.7957% base / +72.6688% severe; core-only +81.3976% base / +69.5108% severe. Full minus core terminal NAV **+USD1246.22 base / +USD1082.15 severe**, while full-minus-core turnover **-USD9092.30 base / -USD14483.73 severe**. Thus total portfolio improved relative to its own core, even with less turnover; this is not a complete gate pass.

Preregistered *full minus leave-one-out* annual net log-growth, 2023 / 2024, carried-before-fill:

| Sleeve | Base 2023 | Base 2024 | Severe 2023 | Severe 2024 | Decision |
|---|---:|---:|---:|---:|---|
| Opportunity | +0.006234 | **-0.006429** | +0.007869 | **-0.005794** | **FAIL** |
| Relative Value | +0.006242 | +0.003857 | +0.009209 | +0.006163 | PASS |
| Stress/Recovery | +0.014774 | +0.009865 | +0.015041 | +0.007463 | PASS |

Opportunity also failed 2024 under new-after-fill: base **-0.006249**, severe **-0.005468**. Its base carried-before-fill marginal final NAV was **-USD6.64** and its marginal turnover **-USD2268.95**, showing its failure is **not reducible to excessive incremental turnover**. Relative Value and Stress/Recovery passed all base/severe annual marginal gates in both funding orderings, but **cannot be promoted separately from a rejected seven-slot candidate**, nor can Opportunity be removed or tuned after results. This artifact documents evidence for an independently preregistered *new complete architecture*, not an ER rescue.

Source-only causal gate PASS, 30/30 physical cells PASS, independent Ubuntu22/24 reproduction PASS, zero audit errors. Training-only performance is not validation, forecast, superiority proof, paper or live authorization. 2025 holdout, XRP, 2026+, Phase083, V14/V15/V99, Frozen and paper untouched.