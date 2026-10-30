# V98 Independent DV — preregistered conditional cash-and-carry rotation (2026-10-25)

**TRAINING ONLY, not a qualified engine.** Hypothesis locked before any DV PnL. DU and all earlier rejected architectures remain rejected; this is NOT a DU rescue, a core-only promotion, a parameter grid, or a post-result selection. No 2025+, XRP, contaminated Phase083 or external V14/V15/V99 inputs.

Economics: rather than DU's signed BTC time-series market beta, DV starts from *cash* and buys only trailing native-funding-adjusted positive leaders. Each satellite must pass a pre-trade estimated edge-versus-friction filter; funding spread is a separate carry trade, not a price-momentum long/short pair. Positions share the same CG 60%-buffered physical risk governor and next-open settlement.

Seven slots, all fixed before results:
1. **Growth Core:** every 168 completed 1h closes, compute 336h net log price return minus realized native funding; long the two strongest positive net assets at weights 60%/40%, or 100% the only positive asset, or cash if none. Never short core.
2. **Opportunity:** within positive 336h net trend, 24h price pullback below -0.5% followed by 6h bounce above +0.1%, with 72h/prior-240h quote-volume ratio >0.75. Long the strongest 336h net trend among eligible; expected rebound proxy 0.5 times pullback magnitude minus 0.3% friction must be positive.
3. **Relative Value:** select lowest and highest realized *native* 64h funding accumulations (8 settlement events), 50% long cheapest and 50% short most expensive; activate only if projected 168h funding advantage, based solely on prior 64h, exceeds 0.08% expected round-trip friction. No price-spread sign selection.
4. **Stress/Recovery:** when BTC 72h return below -2.5% and last 6h negative, 50/50 short BTC/SOL; when BTC 72h below -1% but last 6h above +0.5%, 50/50 long BTC/SOL. Mutually exclusive.
5. **Regime Router:** RISK_ON if BTC net336 positive and at least 2 of 4 assets positive; RISK_OFF if BTC net336 <-3% and at most one positive; else MIXED.
6. **Dynamic Allocator:** nominal (Core,Opportunity,RV,Stress) RISK_ON=(3.2,.20,.16,.16), MIXED=(2.6,.16,.18,.22), RISK_OFF=(.7,.12,.18,.40), with Opportunity and RV switched to cash if their stated ex-ante friction gates fail. No future return or realized strategy PnL used for allocation.
7. **Risk Governor:** existing unchanged CG buffered 60% stressed-NAV reserve, 81-corner next-open physical feasibility, native funding, conservative mark and staged exit; no hidden borrowing.

Source activity gate BEFORE any DV system PnL: per 2023 and 2024 minimum active 168h epochs Core>=4, Opportunity>=4, RV>=8, Stress>=4. On failure reject DV without running system PnL.

Economic gate: pinned authenticated Binance USD-M Clean-4 Dec2022–Dec2024 only, warmup 1440h, next actual open execution, USD10k 5 paths (core, full, three leave-one-out) x base/severe/supersevere x both native funding orderings = 30 physical cells; two independent Ubuntu runner reconciliations, causal prefix test, no leakage. Positive 2023 AND 2024 net log growth base and severe both orders; each satellite positive annual marginal net log growth in 2023 AND 2024 base and severe both orders; full 2y CAGR >50% base and >30% severe, severe max DD <45%, turnover <=USD600k, 30/30 physical survival. Record funding, fees, slippage, PF, payoff, win-rate, positive days, concentration, tail risk, and annual growth. Failure means permanent rejection, not tuning.

Only after a complete internally frozen DV passes this training gate may separate 2025 holdout validation be considered; only after that may external benchmarks be opened. No live or paper orders.