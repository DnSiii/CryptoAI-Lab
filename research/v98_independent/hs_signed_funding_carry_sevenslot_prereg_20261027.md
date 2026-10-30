# V98 Independent HS — composed signed funding-carry / relative-strength spread engine

**PREREGISTERED 2026-10-27 BEFORE ANY HS CODE OR PNL.** HR is permanently rejected on its frozen training economics (Opportunity marginal negative and turnover over cap); HS is not a parameter/sign/window/cost rescue of HR. This is a distinct **real long/short collateralized** portfolio financing hypothesis, based on native signed 8h funding carry and cross-asset spreads rather than HR spot-volume displacement. No use of V14/V15/V99 internals.

## Immutable data, physical execution, independence
Only SHA-pinned Binance USD-M Clean-4 BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT 1h OHLCV, native signed 8h funding, mark and conservative liquidation/exit liquidity. Dec-2022 warmup, 2023-2024 chronological TRAINING ONLY; no XRP, 2025 untouched holdout, 2026+, Phase083, V14/V15/V99 internals, Frozen, paper or live. All signals computed after completed t close, executed at actual t+1 open. Signed shorts require actual collateral, fees, funding and 81-corner adverse liquidation; no synthetic borrow, fake leverage or upside ceiling.

## Seven frozen slots; no grid or fitting
1. **Growth Core:** every 168h, long top two 336h funding-net trend / 168h downside semivol floor .002, weights 60/40. No short Core.
2. **Opportunity:** **signed funding-carry spread**. Among four assets, long 75% of this sleeve in the asset with the lowest prior 336h native signed funding burden (short crowding); short 25% in the highest-burden asset (long crowding). Rank by funding history only, not future prices, no post-result sign flip.
3. **Relative Value:** **relative-strength spread**. Rank prior 168h funding-net log-return, long strongest asset at 65% of sleeve gross and short weakest at 35%, distinct from the funding-carry Opportunity. Stable tie-break by Clean-4 order.
4. **Stress/Recovery:** if median 72h funding-net log-return < -.08, long strongest 72h asset 25% and short weakest 75% of this sleeve's gross; otherwise long strongest 24h funding-net return 100%. The stress short is real signed USD-M collateralized exposure, not a synthetic negative cash return.
5. **Regime Router:** STRESS if median 72h funding-net log-return < -.08; TREND if >=3 assets have positive 336h funding-net return; TRANSITION otherwise.
6. **Dynamic Allocator:** deterministic regime budgets (Core, Opportunity, RV, Stress): TREND (.55,.20,.15,.10), TRANSITION (.45,.25,.20,.10), STRESS (.35,.25,.20,.20). Gross requested TREND .72, TRANSITION .70, STRESS .65. Signed pair gross, not net, consumes budget; ablated sleeves' budgets finance Core in independently funded counterfactual books.
7. **Risk Governor:** unchanged GL order-invariant conservative 81-corner physical governor, native funding/mark, fees/slippage and staged exit liquidity. No relaxation for shorts.

## Gates before any promotion
Source-only compile, exact signed funding provenance, future mutation invariance, at least 8 financed epochs per optional sleeve in BOTH 2023 and 2024. Then 5 independently funded physical books × 3 fee tiers × 2 funding orders = 30 cells on two Ubuntu versions; independent each-hour settlement/funding replay, 2023/2024 annual net growth, severe/supersevere, DD, tails, concentration, PF, payoff, win rate, positive days, turnover. Preregistered economic minima (screen, NOT objective): annual net log-growth positive base/severe, base CAGR >50%, severe CAGR >30%, severe DD <45%, base/severe turnover <=USD600k; each optional sleeve full-minus-physical-ablation two-year log growth >+.02 in base/severe both funding orders, each year >=-.03. Any failure -> permanently reject HS, no sign/threshold/window/gross rescue. Only after full independent training PASS freeze complete HS, then separate validation/2025 holdout and later external benchmarks. Ultimate target remains materially superior long-run compounded wealth, not mere threshold compliance.

No HS PnL or performance has been measured by this preregistration.
