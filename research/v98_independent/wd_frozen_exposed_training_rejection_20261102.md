# V98 WD — frozen exposed-training rejection (2026-11-02)

**FINAL: REJECT_WD_EXPOSED_TRAINING. NOT A V98 CHAMPION.** Hypothesis preregistered before code/results in commit `46fd86ca48cf217fe9c87a18bc5036befa75b1b8`: BTC-led alt information propagation, seven complete portfolio slots, no benchmark tuning or post-PnL sign/window/gross rescue. Run [41448382464](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41448382464) completed all 30 historical physical ledgers and separate source/cash/funding oracle; CI intentionally red at economic reject gate. Initial synthetic code indexing error was corrected **before any historical PnL**, not a strategy change.

## Authenticated exposed training, not independent future validation

Clean-4 BTC/ETH/BNB/SOL Binance USD-M 1h; Dec-2022 warmup through Dec-2025 (2023-25 exposed training); 27,048 hours, 13,524 native funding events, 1,096 t-1 causal decisions. Source incidence: Growth 1,096; Opportunity 172; RV 1,096; Stress 1,096; all prereg >=109. Five books x three one-way illustrative cost tiers (10/20/35 bps) x two funding settlement orders = **30/30 completed physical cells**. USD10k initial NAV; conservative official hourly mark envelopes, not exact exchange funding ticks.

| WD full, carried-before-fill | Base | Severe | Supersevere |
| --- | ---: | ---: | ---: |
| Annualized compounded CAGR | **-23.4831%** | **-36.9940%** | **-52.9451%** |
| Terminal NAV USD | 4,479.94 | 2,501.18 | 1,041.87 |
| Max drawdown | -60.9274% | -77.2828% | -90.4181% |
| 2023 net return | -24.4214% | -37.9955% | -53.9494% |
| 2024 net return | -27.4957% | -40.2098% | -55.2475% |
| 2025 net return | -18.2459% | -32.5328% | -49.4454% |
| Illustrative trading costs USD | 4,104.24 | 6,519.94 | 8,451.55 |
| Signed native funding USD | -292.27 | -237.23 | -178.33 |

Base marginal log growth vs leave-one-out: Opportunity **-0.15459**, RV **-0.24035**, Stress **-0.28566**. Severe: **-0.17973**, **-0.37173**, **-0.31520**, respectively. **20 binding prereg economic failures** across both funding orders (base/severe CAGR, severe DD and negative annual returns, all three optional negative marginals). Core-only results are diagnostic, NOT permission to rescue WD. No post-result retuning, no champion promotion.

**Independent audit:** separate beta/residual/volatility signal recomputation; 27,048 hourly cash/fill/funding rows, 13,524 native events, 1,096 decisions and **378,675 reconciled accounting identities**, exact base NAV USD4,479.93769424, fee USD4,104.23820376, funding -USD292.26650213. Intentional cash adulteration detected. [Action log and artifacts](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41448382464).

**Remaining blockers:** original exchange-origin 13,524 funding settlement markPrice ticks with independently verifiable provenance; account-specific dated fee tiers, historical spread/depth/impact and collateral/liquidation proof; separate chronological validation and untouched future holdout. HTTP451 exchange API restriction can be addressed only by authorized independently attested original export, not fabricated or hourly surrogate marks. No V99/V16 Frozen, V99 research, 2026+, XRP, contaminated Phase083 or paper state touched. No live trading authorized. WD stays frozen rejected.
