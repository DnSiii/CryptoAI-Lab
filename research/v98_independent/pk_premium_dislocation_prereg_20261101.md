# V98 PK — premium dislocation and convergence, seven-slot composed portfolio (pre-PnL registration, 2026-11-01)

Binding **before implementation or PK return inspection**. Clean-4 Binance USD-M BTC/ETH/BNB/SOL 1h, 2022-12-01 through 2025-12-31 **exposed training only**. 2026+, Phase083, XRP, V14/V15/V99, Frozen and paper forbidden. No reuse of rejected PJ/PI/PH/PG strategy signals or thresholds; only independently audited physical executor, cash accounting and Clean-4 source bridge.

## Hypothesis and economics
The newly authenticated exchange-native premium-index hourly history (108,192 asset-hours; canonical CSV SHA256 `c301a38642f229ca2746ae33baaf58e4bb21ac280a1a99dbbc328cc074caaad4`) measures persistent futures-vs-index dislocations. A large premium discount with recovering spot momentum may predict price/carry normalization; cross-sectional relative premium may predict convergence; extreme discount after selloffs may predict rebound. Unlike channel breakouts, the independent explanatory variable is premium dislocation. A seven-slot *composed* engine is falsified if optional sleeves do not add net marginal log wealth to the full portfolio. No post-result sign/threshold rescue.

## Causal data rule
The premium CSV is keyed by **bar OPEN UTC**, so at weekly decision time t (close of price bar t), premium bar t is NOT yet complete: only premium_close[t-1] and earlier may be used. Price close[t] and earlier permitted, order at price open[t+1]. Verify 27,048 hourly timestamps per asset, SHA256 and strict asset order; source funding 13,524 native events with conservative mark envelope, NOT exact funding-event markPrice. Premium is NOT substituted for missing markPrice. Every feature must be finite; never forward-fill.

## Locked signals (one weekly decision every 168h from t=744 to 26952)
Let P_j= premium_close[t-1,j], B_j=median(premium_close[t-168:t,j]), S_j=std(premium_close[t-672:t,j]) floored at 0.0002, Z_j=(P_j-B_j)/S_j, D_j=P_j-premium_close[t-25,j], R_j(k)=log(price_close[t,j]/price_close[t-k,j]); all ties asset index. Define `discount` if median(Z)<-0.6, `crowded` if median(Z)>+0.6, else `balanced`.

1. **Growth Core:** eligible if R(336)>0 and Z<+0.5 and R(72)>-0.06. Rank eligible by R(336)/max(std(336 hourly price returns)*sqrt(336),0.04); top 2 long +0.40/+0.22. If no eligible, cash; never short in core.
2. **Opportunity:** among Z<-1.0 and D>0 and R(24)>0, long most negative Z +0.20; else cash.
3. **Relative Value:** among non-BTC assets, if Z spread >1.6, short max-Z and long min-Z at 0.12 each, only when D[min]>D[max]; else cash. Dollar-neutral, not guaranteed beta-neutral.
4. **Stress/Recovery:** if BTC R(72)<-0.10 and BTC Z<-1.2 and D_BTC>0, long BTC +0.18 (discount rebound); if BTC R(72)>+0.10 and BTC Z>+1.2 and D_BTC<0, short BTC -0.18 (overheated unwind); else cash.
5. **Regime Router:** `discount`: priority Opportunity,Stress,RV; `crowded`: RV,Stress,Opportunity; `balanced`: RV,Opportunity,Stress.
6. **Dynamic Allocator:** retain core; optional budget min(0.30,0.84-core gross). For each optional in priority order, use min(raw gross,room) and scale linearly. Recompute all leave-one-out portfolios from raw sleeves, never retrofit.
7. **Risk Governor:** total target gross <=0.84, core <=0.62, optional <=0.30; original physical hourly gap/intrabar/funding/NAV, atomic one-way fills, zero-volume fill veto. Costs base 4/2 bps, severe 10/10, supersevere 15/20; both funding orders.

## Binding gates
Causal future-mutation test on price, premium and funding; independent signal/allocator oracle for all 157 decisions and 5 books; full/core-only/minus Opportunity/minus RV/minus Stress x 3 cost tiers x 2 funding orders = 30 physical cells; separate independent hourly cash and fee/slippage/funding accounting; independent receipt gate and four tamper tests. Require 30 feasible, base CAGR >80%, severe >60%, severe max DD >-45%, positive each 2023/24/25 severe, base/severe turnover <=USD 1m on USD10k, optional sleeve net log-growth marginal >0.02 in base and severe both orders, no optional yearly log marginal below -0.03. Any failure => permanently reject PK without tuning. Passing training is **provisional only**, not validated or authorized. Report annual, PF/payoff/win, positive days, tail and concentration.

## Known blocking evidence
Still lack 13,524 official funding-event `markPrice` objects with symbol, fundingTime, fundingRate, markPrice, original exchange HTTP request/response headers and pages, SHA256, authorized custody; API HTTP 451. Authorized raw exchange export is alternative. Untouched prospective validation and final holdout are not available. No claims of live execution, external superiority, paper or deployability.
