# V98 Independent WL — preregistered complete seven-slot funding-buffer compound engine (2026-11-02)

**Freeze BEFORE any Clean-4 economic PnL.** New WL is a distinct architecture hypothesis, not a rescue, revision, or re-ranking of rejected V98 candidates. The static six-book funding diagnostic is used **only** to specify a survival constraint; its BNB result is explicitly prohibited as a selection signal. V14/V15/V99 must not be inspected.

## Fixed source and chronology
Clean-4 BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT, Binance USD-M 1h, Dec-2022 warmup and 2023-01-01 through 2025-12-31 exposed training. Four-source hash-pinned 2025 bridge, 27,048 hours, 13,524 native 8-hour funding calendar/rate events. Funding marks remain conservative hourly envelopes, **not** original settlement marks. 2025 is exposed training, **not** independent validation. No XRP, 2026+, Phase083, holdout, Frozen, paper or benchmark reads.

## Seven integrated slots; deterministic causal signals
Daily decision after 23:00 UTC close; trade no earlier than next 00:00 UTC open. At t use only candles and funding observed by t.
1. **Growth Core:** positive 336h and 72h log-price trend, top two assets by predeclared combined score, 0.19 each (0.38 gross) when breadth of positive 336h trends >=2, otherwise 0.09 each; no short in core.
2. **Opportunity Sleeve:** first-ranked asset with 24h log return >0.04 and close above the previous 96 hourly highs, 0.12 long; otherwise inactive.
3. **Relative-Value Sleeve:** if cross-sectional 72h log-return spread >0.08, 0.05 long weakest and 0.05 short strongest; otherwise inactive.
4. **Stress/Recovery Sleeve:** if 336h equal-weight market drawdown below -0.12, 24h equal-weight rebound positive and <=2 positive 336h trends, 0.10 long strongest 24h rebound; otherwise inactive.
5. **Regime Router:** when breadth <2, scale core/opportunity/RV to 0.60/0.50/0.50; otherwise 1.0. Stress remains unchanged.
6. **Dynamic Allocator:** combine four sleeves without parameter search; proportional cap at 0.70 absolute gross, no explicit upside target or leverage.
7. **Risk Governor:** at each next-open, including every hour between daily decisions, track cash, quantity, gap PnL, fees, signed native funding, mark-envelope adverse risk and physical exposure. On daily signal trade to target <=0.70 gross. Between daily decisions, if gross/cash >0.75 **or** (cash-gross)/cash <0.22, trim all positions proportionally to 0.65 gross. If either settlement/fill ordering breaches gross<=cash, 10% maintenance or intrahour adverse maintenance before possible next fill, **fail physically**, do not post-hoc rescue. No future funding-rate foresight.

## Precommitted testing
Run full portfolio and core-only, minus-opportunity, minus-RV, minus-stress, each across 10/20/35 bps illustrative one-way all-in costs and carried-before-fill/new-after-fill funding orders = 30 physical 27,048-hour cells. Terminal flat close with fees. Report CAGR, 2023/2024/2025 annual return, max drawdown, funding, costs, concentration, tails, PF/payoff/win-rate, positive days, source and causality checks. Each sleeve must contribute positive marginal log growth to full system in base and severe, with no failed survival cells. Precommitted growth aspiration is **>80% CAGR base and >60% severe**, DD no worse than -45% severe, every year positive severe; failing any is rejection, not retuning. The 80/60 hurdles are economic aspirations, **not a ceiling**. No tuning based on observed results.

## Audit and stop conditions
Separate accounting oracle must reconcile the physical hourly ledger independently, catch intentional tampering, and check causal future mutation. This workflow is exposed-training research only. No candidate approval until independent chronological validation (not 2025), original 13,524 exchange settlement marks, account-dated fees, order-book liquidity/impact and collateral/liquidation schedule have verified provenance, plus untouched future holdout and gates. Never claim paper/live readiness from this experiment.
