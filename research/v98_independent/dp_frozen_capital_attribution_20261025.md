# V98 DP — independent frozen capital attribution (2026-10-25)

Frozen source run [40186440175](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40186440175), artifact-only forensic run [40186609122](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40186609122). DP remains **REJECTED**; no new PnL computation or parameter changes.

USD10k base carried-before-fill: core-only CAGR **49.4334%**, full CAGR **51.8766%**; 2023 core +38.2669%, full +47.7611%; 2024 core +61.5906%, full +56.1960%. Severe: core-only CAGR **48.3744%**, full **50.0559%**. Full native funding **-USD1911.30** base and **-USD1867.96** severe; base fees+slippage USD72.41, severe USD354.15; turnover USD72410.42 base, USD70830.45 severe. Full max gross/NAV 0.7673 base, 0.7622 severe, single-asset concentration 0.7362 base. Base hourly PF 1.0431, payoff 0.9767, win rate 51.64%, 352 positive UTC days, 1% hourly CVaR -1.5710%. These are historical training diagnostics.

Strict marginal annual net log-growth (full minus leave-one-out, base carried-before-fill):
- Opportunity: 2023 **+0.049936**, 2024 **-0.008448**.
- Relative Value: 2023 **+0.014374**, 2024 **-0.021691**.
- Stress/Recovery: 2023 **-0.000383**, 2024 **-0.001239**.
Severe signs unchanged. Full outperforms core-only in 2y aggregate but damages 2024 growth and fails each satellite's robust marginal gate. All 30 physical cells survived and both Ubuntu runners reproduced, with one pinned source manifest hash. No holdout or external benchmarks accessed.

**Structural physical constraint (not a performance forecast):** CG's 60% stressed NAV buffer with 40% initial long shock and 24h -1% adverse continuation implies a first-order long-only gross/NAV upper bound about 0.757 (before funding, fees, maintenance and interaction); 65% initial short shock plus 24h +1% continuation implies short-only bound about 0.365. This explains why requested nominal gross >2 does not translate into executable leverage. Do not relax survival constraints to inflate backtests.

Next independent economic thesis must deliver positive per-year net marginal contributions and account for physical gross asymmetry; rejected DP cannot be rescued.
