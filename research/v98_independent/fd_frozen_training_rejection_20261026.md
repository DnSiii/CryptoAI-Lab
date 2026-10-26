# V98 Independent FD — immutable training rejection; risk-budget root cause resolved, alpha gates failed (2026-10-26)

Preregistered before any FD PnL in `8301719675bc0cae57bce2f62c7953609d32366e`. A complete seven-slot **single physical book** with zero-sum opportunity/RV/stress score tilts, one normalized long-only target every 240h, and unchanged 60% stressed-NAV physical governor. Authenticated Clean-4 Dec-2022 warmup + 2023–2024 training only. 2025 holdout, 2026+, XRP, contaminated Phase083, V14/V15/V99, Frozen, paper and live untouched.

## Verified execution
- Workflow https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40277004899.
- Source-only causal future mutation and gross/normalization conservation PASS. 2023 active epochs core/opportunity/RV/stress **37/14/37/21**; 2024 **37/12/37/22**; all preregistered >=4 gates PASS.
- **30/30** native physical USD10k cells survived; cross-OS numerical reproduction PASS; artifact-only audit errors []; full annual positive growth gates PASS. Five independent signed all-hour ledger oracles PASS: **526,290 settled-hour checks and 65,760 native funding-event-hour checks**, no divergences. Ledger correctness does not establish positive alpha.

## Actual native training economics (carried-before-fill)
- Full base CAGR **+89.874598%**, end NAV USD**36,084.02**, 2023 **+147.539687%**, 2024 **+45.770653%**. Severe CAGR **+85.317938%**, end NAV USD**34,371.75**, 2023 **+141.415671%**, 2024 **+42.375813%**. Max drawdown base **29.538358%**, severe **29.833285%**.
- Full base turnover **USD249,753.57**, severe **USD238,512.70**, both below USD600k. Only **74 physical fill hours**, compared with FC full 731; the single-book allocator removed the separate-sleeve churn and restored turnover discipline.
- Base fees + slippage USD**249.75**, signed native funding **-USD2,401.94**; severe fees + slippage USD**1,192.56**, funding **-USD2,304.28**. Peak gross/NAV **0.77864**; peak single-asset gross concentration **73.19%**. Base hourly PF **1.04329**, payoff **0.98030**, win rate **51.56%**, positive UTC days **378/731**, worst-tail hourly CVaR 1% **-1.886%**.
- Core-only CAGR **+86.472% base**, **+83.185% severe**, turnover base USD**158,331**. Removing RV from FD increases full base CAGR to **+94.425%** and severe to **+90.382%**. Removing Stress yields base **+90.293%**; removing Opportunity yields base **+83.296%**.
- Locked annual marginal net log-growth FAIL: Opportunity base 2023 **+0.0725316**, 2024 **-0.0019634**; severe 2023 **+0.0716335**, 2024 **-0.0043996**. Relative Value base 2023 **-0.0455454**, 2024 **-0.0018482**; severe **-0.0470107/-0.0069426**. Stress/Recovery base **-0.0071889/+0.0027848**; severe **-0.0073100/+0.0019256**. Both funding orderings fail the same preregistered annual gates.

**FINAL: REJECT_FD_HISTORICAL_GROWTH_OR_MARGINAL.** This is a real architectural result: source, causal execution, 30-cell physical survival, independent ledger, annual full growth, severe drawdown and turnover all pass, but each of three sleeves fails its own strict marginal annual gate. Do not relax gates, revise FD signs/windows/thresholds, reclassify this as a complete engine, or access 2025 validation/benchmarks. Next research must supply *new independently preregistered predictive economic edge*, not merely rearrange or leverage these rejected score tilts. No live authorization.
