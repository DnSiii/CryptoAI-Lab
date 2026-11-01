# V98 PI — positioning elasticity with confirmed directional continuation (preregistered 2026-11-01)

**Binding pre-result architecture.** Commit before PI executable, oracle, workflow, any simulated PnL or inspection of PI outcomes. This is an independent seven-slot composed portfolio hypothesis, not a retune of rejected PG (OI stock/quote-flow), PH (funding crowding/carry), PF (historical marginal allocator), or OT (price-only breadth reversal). No rejected candidate is revived. 2022-2025 is **exposed training**, including 2025; 2026+, contaminated Phase083 holdout and V14/V15/V99 remain inaccessible.

## Economic mechanism and falsification

New open interest is not by itself an edge. PI tests whether *price displacement confirmed by expanding outstanding positions* predicts a continuation in the direction of price discovery; in a different slot, relative price movement unexplained by proportional position growth may reveal leader/laggard divergence. Stress responds to exceptional realized volatility rather than assuming OI liquidation is automatically a profitable reversal. Full seven-slot incremental net log wealth, not isolated hit rate, is the target. If optional sleeves do not contribute after costs, reject PI permanently, do not reverse their signs or tune thresholds.

## Locked source and causal clock

Clean-4 BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT Binance USD-M 1h from 2022-12-01 warmup to 2025-12-31. Use pinned 2022-24 and 2025 OI with vendor ZIP SHA, 106,920 verified asset-hours and 1,272 quarantined; 143/157 eligible 168h weekly decisions, 14 ineligible. OI-dependent Opportunity, RV and Router are disabled if any of the four assets has a missing OI hour in t-167..t. Growth and Stress are price-only and may still run. Signed native funding 13,524 events, conservative hourly official mark envelope (not exchange-event tick), original fill and cash ledgers, zero-volume execution fail-closed. Decisions t=744,912,...,26952; execution at open[t+1]. Only completed <=t observations, with deterministic asset-index tie-breaks.

Features: rN_j=ln(C_j[t]/C_j[t-N]), OI72_j=ln(OI_j[t]/OI_j[t-72]), OI168_j=ln(OI_j[t]/OI_j[t-167]); sigma504_j=std(504 completed 1h log returns)*sqrt(504). V24_BTC=std(24 completed hourly BTC log returns); V168_BTC=std(168 completed hourly BTC log returns).

## Seven-slot portfolio

1. **Growth Core (price trend)**: if BTC r504>0 and >=2 assets r504>0, select up to two assets with r168>0 ranked descending by (r504+0.5*r168)/max(sigma504,0.03), weights +0.38,+0.20. If BTC r504<0 and <=1 asset r504>0, select up to two assets with r168<0 ranked ascending by same quality, weights -0.34,-0.18. Else cash. Max core gross .58.
2. **Opportunity (positioning elasticity continuation)**: candidates require OI72>+0.06. Long if r72>+0.06 and r24>+0.01; short if r72<-0.06 and r24<-0.01. Rank by descending |r72| then index; at most one asset, signed .22. No funding-rate sign filter or price reversal filter.
3. **Relative Value (price discovery vs positioning)**: score_j=r168_j-0.5*OI168_j. Rank high and low by score. If score spread>0.15, high r72>0, low r72<0 and |OI168_high-OI168_low|<0.25, long high +.14 and short low -.14. No funding dispersion or price mean-reversion condition.
4. **Stress/Recovery (volatility shock continuation)**: when V168_BTC>0 and V24_BTC/V168_BTC>1.8, short BTC -.18 if BTC r24<-.05 and BTC r168<0; otherwise long BTC +.18 if BTC r24>+.05 and BTC r72<0. Otherwise cash. Price-only, even with OI gaps.
5. **Regime Router**: if OI ineligible, mode unknown. Else mode expansion if >=3 assets OI168>+.025; contraction if >=3 assets OI168<-.025; neutral otherwise. Priority expansion=(Opportunity,RV,Stress), contraction=(Stress,RV,Opportunity), neutral/unknown=(RV,Opportunity,Stress).
6. **Dynamic Allocator**: preserve core. Optional budget min(.32,.84-core gross). Iterate fixed priority, compare 168 completed hourly signed portfolio return paths for candidate and already allocated weights. If correlation >.35 halve requested gross; else full. Proportionally clip to remaining budget; never optimize on realized PnL, no gross renormalization. Recompute all ablations independently.
7. **Risk Governor**: decision virtual gross <=.84, optional <=.32, core <=.58, no hidden leverage; pretrade, open-gap, intrabar, funding and post-trade NAV checks with original one-way atomic physical executor. Base fee/slip 4/2 bps, severe 10/10, supersevere 15/20; both funding orders.

## Binding tests and gates

Synthetic future mutation of price/OI/funding; OI-missing window fail closed (slots 1,2 and OI router, **not** price-only Stress), independent scalar signal and allocator oracle. 30 physical historical cells: full, core-only, minus Opportunity, minus RV, minus Stress x three cost tiers x two funding orders. Independent cash and fill reconciliation, receipt arithmetic and tamper rejection. All 30 physically feasible; base CAGR >80%, severe CAGR >60%, severe DD better than -45%, each 2023/24/25 severe annual return positive, base/severe turnover <= USD1m from USD10k. Every optional sleeve full-minus-ablation marginal log growth >+.02 in base and severe for both funding orders; each annual marginal >=-.03. Report PF/payoff/win-rate as **hourly NAV change** metrics (not closed-trade statistics), positive days, tails, concentration, funding, turnover, fees and reproducibility. Any failure => REJECT_PI_TRAINING. A training pass is provisional only.

## Independent delivery gates

The 13,524 exact exchange-origin funding-event markPrice records remain unavailable (HTTP 451 at Binance USD-M historical endpoint). Required fields symbol/fundingTime/fundingRate/markPrice, original request and response bytes/headers, UTC pagination, SHA256 and authorized custody. Alternative: authorized exchange-origin export with independent importer audit. The hourly mark envelope does not substitute for tick attestation. Untouched prospective validation and final holdout remain unavailable; 2025 cannot be relabeled validation. No benchmark opening, paper or live operation.
