# V98 PS — daily stateful trend-inventory composed engine (binding preregistration, 2026-11-01)

**State: PREREGISTERED BEFORE IMPLEMENTATION AND BEFORE PS HISTORICAL PNL.** Distinct economic architecture from rejected PR: daily stateful trend inventory with hysteresis, not path-efficiency ratio or weekly 157-decision strategy. PR and all rejected candidates remain frozen. PS cannot rescue them. No V14/V15/V99 parameters, signals, architecture or results consulted for PS selection.

## Hypothesis and falsification

A medium-horizon directionally persistent inventory, updated daily rather than weekly and protected against frequent turnover by **fixed stateful hysteresis**, may compound more effectively in crypto's episodic trends. A separate breakout sleeve can add convex participation; a hedged relative-value sleeve can diversify during dispersion; stress inventory can contribute in sudden synchronized declines. These are hypotheses, not proven returns. The entire composed portfolio must pass preregistered economic gates and each optional module must have positive marginal contribution. No post-result rescue.

## Immutable training / execution

Clean-4 BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, authenticated Binance USD-M 1h from Dec-2022 warmup through Dec-2025 exposed training, 27,048 hours. Decision t=1008+24k while t<27048; only closed hourly prices/quote volumes and funding observations through t. Execute target on t+1 open; mark/funding at exchange events, both carried-before-fill and new-after-fill. 2025 is exposed training, **not** independent validation. No XRP, 2026+, Phase083, external benchmarks, paper or live.

## Binding deterministic signal design (all logarithmic returns)

At each daily t compute r24, r72, r168, r336, r1008 and sigma336=std(336 completed hourly log returns)*sqrt(336), floored at 0.05. Breadth = number of r336>0. Past 168h signed funding carry is diagnostic only, never used as an oracle for future funding. Ties by Clean-4 order.

1. **Growth Core:** in breadth>=2, rank assets with r1008>0 and r336>0 by (r1008+0.5*r336)/sigma336 descending; target long +.36 and +.18 for top two. In breadth<2, rank r1008<0 and r336<0 by same score ascending; target short -.32 and -.18. Else cash. **Hysteresis:** maintain prior core asset/sign until a new candidate outranks its incumbent score by >=25% of the absolute incumbent score, with floor 0.02; if incumbent no longer eligible, replace immediately. Preserve weights by rank. All hysteresis uses only previous decisions and current t, not future PnL.
2. **Opportunity Sleeve:** 72h breakout: for each asset compare current close with max/min of prior 336 completed closes excluding current 72h; require r72>+.05 and quote-volume last 72h / preceding 72h >=1.20 for upside, or r72<-.05 and ratio>=1.20 for downside. Choose highest abs(r72)/sigma336, ties by asset index. Long +.16 or short -.16, else cash. No use of rejected PR efficiency or PK premium.
3. **Relative-Value Sleeve:** cross-sectional medium-term dispersion, not efficiency convergence: if spread max(r168)-min(r168)>=.22, and the 24h returns of top and bottom assets have opposite signs, long bottom +.10 and short top -.10. Otherwise cash. This sleeve is independently falsifiable.
4. **Stress/Recovery Sleeve:** if breadth<=1 and >=3 assets have r24<-.045, short the asset with lowest r72 at -.14; if breadth>=3 and >=3 assets have r24>+.045 after a 72h broad drawdown (median r72<-.04), long highest r24 +.14; otherwise cash.
5. **Regime Router:** risk-off if breadth<=1, risk-on if breadth>=3, mixed otherwise. Optional priority risk-off=(Stress, RV, Opportunity), risk-on=(Opportunity, RV, Stress), mixed=(RV, Opportunity, Stress).
6. **Dynamic Allocator:** core first; optional gross budget <=.28 and total gross <=.84; in each regime, allocate in priority order, proportionally clipping the last sleeve to remaining budget. Keep distinct virtual positions for independent leave-one-out attribution.
7. **Risk Governor:** use existing independently audited V98 one-way atomic planner, 1h OHLC adverse intrabar solvency, zero-volume fill veto, pre/post fill gross and fee/slip/funding checks; conservative official mark envelope, never call it exact funding-event mark.

## Binding physical/economic proof

Five books PS_full, PS_core_only, PS_minus_opportunity, PS_minus_RV, PS_minus_stress x base fee/slip 4/2 bps, severe 10/10, supersevere 15/20 x both funding orders = **30 physical cells**. Independent scalar decisions/allocator oracle, 26,039 hourly cash and fill reconciliations (27048-1008-1), full source pins, future-mutation causal test, independent receipt arithmetic and four tamper controls. All 30 physical cells must pass. Base CAGR >80%; severe CAGR >60%; severe max drawdown >-45%; all severe annual 2023, 2024, 2025 >0; turnover <=USD1m from USD10k in base and severe; each optional leave-one-out marginal log growth >.02 in base and severe, both orders, and each annual log marginal >=-.03. Failure means permanently reject PS, no post-result sign/window/threshold/gross/cost rescue. Report concentration, tails, Profit Factor, payoff, hourly win rate, positive days; do not mislabel hourly NAV metrics as trade-level.

## External requirements

The 13,524 exact Binance funding-event markPrice values remain absent due HTTP 451, requiring authorized exchange-origin raw fundingRate response pages or equivalent export, original URLs/headers/UTC retrieval/SHA256 and independently verified custody. The envelope is conservative exploratory proxy only. Account-specific historical fee tiers, executable bid/ask/depth/impact and untouched chronological validation/prospective holdout are also required. PS cannot be called final without them; no real/paper trading.
