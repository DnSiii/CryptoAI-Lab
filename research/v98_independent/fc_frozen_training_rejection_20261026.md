# V98 Independent FC — immutable training rejection and root-cause audit (2026-10-26)

Preregistered before FC PnL in `32a0ddd9360111cafc2bcadf86fb322cb96b9184`. Complete asynchronous four-clock seven-slot engine. Only authenticated Clean-4 Dec-2022 warmup and 2023–2024 training; 2025 holdout, 2026+, XRP, Phase083, V14/V15/V99, Frozen and paper untouched.

**Run:** https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40276581995. Source-only future-mutation PASS; 2023 active epochs core/opportunity/RV/stress = **37/85/111/306**, 2024 **37/81/116/309**, all >=4. **30/30** physical USD10k cells survived; cross-OS reproduction PASS, independent artifact-only audit errors []; all four annual full-growth gates PASS. Independent five-book hourly settlement oracle **526,290 settled-hour checks and 65,760 funding-event-hour checks**, no mismatches; ledger correctness does not establish alpha.

## Native training economics (carried-before-fill)
- Full base 2023–2024 CAGR **77.297723%**, ending USD**31,459.13**, 2023 **+125.866784%**, 2024 **+39.281810%**. Severe CAGR **61.769939%**, ending USD**26,186.75**, 2023 **+105.518098%**, 2024 **+27.418221%**. Severe max DD **36.930616%**, base max DD **35.220049%**.
- Full base turnover **USD878,735.99**; severe **USD769,652.16**; both exceed locked USD600,000. Base fees + slippage **USD878.74**, native funding **-USD1,820.84**; severe fees + slippage **USD3,848.26**, funding **-USD1,588.92**.
- Core-only base CAGR **68.14%**, 2024 **+45.08%**, turnover **USD229,797.48**; core-only severe CAGR **63.50%**, 2024 **+41.48%**, turnover **USD218,760.23**.
- Full base physical fill hours **731** vs core-only **74**, while full peak gross/NAV **0.75904** vs core-only **0.77611**. This confirms the incremental sleeves increased turnover and **displaced** core under the buffered governor rather than increasing effective risk-budgeted exposure.
- Locked marginal annual log-growth FAIL: Opportunity 2023/2024 base **+0.0028075/+0.0075021**, but severe **-0.0005788/-0.0021242**; Relative Value base **-0.0086533/-0.0191391**, severe **-0.0096370/-0.0181158**; Stress/Recovery base **+0.0034704/-0.0215319**, severe **-0.0143989/-0.0392319**. These are carried-before-fill; other funding ordering also fails.

**FINAL: REJECT_FC_HISTORICAL_GROWTH_OR_MARGINAL**. Physical correctness and historical gross CAGR do not override marginal annual and turnover failures. No post-result parameter rescue. A genuinely distinct FD architecture was preregistered before its own PnL to test one combined normalized portfolio within the same physical risk budget; it is not an FC revision. No 2025 validation, benchmarks or live authorization.
