# V98 NK — frozen original training forensic: monthly sleeve PnL vs signed funding (2026-10-30)

**READ-ONLY DIAGNOSTIC OF REJECTED NK. NOT A NEW CANDIDATE, RETUNE, OR APPROVAL.** Original immutable physical workflow https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41084687737, artifact `12991795180`; original 17,543-hour JSONL SHA256 `0981e7613b24c0a8b4d63f903d9ddf45041cb6af3805e8453f92c2cfbbfc2add`. Independent source data from SHA-authenticated Clean-4 training artifact `12549265452`, not 2025+.

**Method:** for each t=745..18287 and virtual sleeve k, independent mark-to-market cash `sum_j qty_before[k,j]*(open[t,j]-close[t-1,j]) + qty_after[k,j]*(close[t,j]-open[t,j])`; aggregate by UTC month/year. Net exchange fees+slippage and signed funding are reported separately because one-way exchange netting and funding across offsetting virtual sleeves cannot be uniquely assigned to one sleeve. Reconciliation of every hourly change `equity_close-equity_before = sum_k sleeve_price_pnl - fees - slippage + signed_funding` had maximum absolute residual <1e-6 USD.

**Original 2023–24 USD price-PnL attribution (NOT causal ablation):**
- Growth Core **+3,433.11** (2023 +2,916.76; 2024 +516.36).
- Opportunity **+926.88** (2023 -211.84; 2024 +1,138.72).
- Relative Value **-445.99** (2023 -13.14; 2024 -432.84).
- Stress/Recovery **+708.89** (2023 +292.84; 2024 +416.04).
- Net execution fees+slippage **-342.31**; signed worst-envelope native funding **-860.37**.
- Reconciled net profit **+3,420.21**, USD10k -> USD13,420.21 (base CAGR +15.8340%). This is historical training only.

**Worst six monthly net equity changes:** 2023-06 -17.47%, 2023-03 -17.14%, 2024-08 -14.20%, 2024-09 -9.23%, 2023-02 -8.00%, 2024-01 -7.94%. Largest Growth Core price-PnL losses: 2023-03 -USD1,619.36, 2024-09 -USD1,472.52, 2024-08 -USD1,421.83, 2023-06 -USD1,010.40. Best months: 2023-10 +30.16%, 2023-12 +26.09%, 2023-11 +23.61%, 2024-03 +16.54%, 2023-07 +16.30%, 2024-11 +15.52%.

**Interpretation without rescue:** structural Core exposure experienced deep whipsaws; Relative Value contributed negative direct price PnL and independently negative marginal log growth (base -.0370, severe -.0377); signed native funding was a material negative drag; Stress had positive direct PnL and positive marginal growth but cannot compensate for weak complete-engine CAGR and severe DD. Opportunity gross price PnL is positive overall but causal ablation marginal growth is below +.020 gate, demonstrating that gross sleeve price PnL cannot substitute for full-portfolio marginal evidence. A genuinely different next engine must address *portfolio compounding under regime transitions*, not cosmetically change the rejected NK thresholds.

**No new PnL or revised candidate:** original 30/30 physical cells, all-hour accounting and independent fill/decision audits remain frozen. Exact event funding markPrice unavailable (HTTP451); conservative official worst-side envelope disclosed. No 2025/2026, XRP, Phase083, external V14/V15/V99, Frozen, paper or live state accessed.
