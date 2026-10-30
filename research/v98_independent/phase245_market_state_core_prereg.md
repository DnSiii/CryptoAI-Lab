# V98 Independent Phase245 — Clean-4 Broad Market-State Growth Core

Status: PREREGISTERED BEFORE PHASE245 PNL.

## Distinct hypothesis
Phase245 does not reuse Phase244 per-asset channel states. It treats Clean-4 as one broad crypto market and trades **common market beta** only when independent short/medium market horizons and cross-asset breadth agree. It is a portfolio-level market-state core, not a cross-sectional rank, residual alpha, channel breakout, macro overlay, or volatility-compression rescue.

## Frozen data
Authenticated Phase243 Clean-4 only: BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT; Dec-2022 warmup through 2025-12; native PIT funding. XRP quarantined. No 2026+, V14/V15/V99.

## Frozen single specification
At each 23:00 UTC close(t), execute at the next 00:00 UTC open:
1. Build equal-weight Clean-4 market log-return index from hourly closes.
2. Compute market index return over prior 30 days (720h) and prior 120 days (2880h), both ending at close(t).
3. Compute each asset's 30-day close return ending at t.
4. BULL state if market 30d > 0 AND market 120d > 0 AND at least 3/4 asset 30d returns > 0.
5. BEAR state if market 30d < 0 AND market 120d < 0 AND at least 3/4 asset 30d returns < 0.
6. Otherwise FLAT.
7. BULL target = +0.25 each asset; BEAR = -0.25 each; FLAT = zero.
8. Hold the daily target between scheduled decisions. Gross cap = 1.0. No leverage scaling.

No alternate horizon, breadth threshold, rebalance clock, sign, asset subset, stop, volatility target, regime overlay or rescue is allowed.

## Execution / stress
Existing exact causal V98 backtester.
BASE 7 bp/side + funding 1.00/1.00.
SEVERE 12 bp + funding debit/credit 1.25/0.75.
SUPERSEVERE 20 bp + 1.75/0.50.

## Frozen passive reference
Before seeing Phase245 results, define a Clean-4 equal-weight long-only reference: +0.25 each asset continuously from the first 2023 open, using the same exact backtester, costs, funding and gross cap. It is diagnostic and an additional Growth-Core hurdle; it does not tune Phase245.

## Promotion gate
Same Phase244 Growth-Core gates:
- BASE return >100%, CAGR >25%, PF>1.10, DD>=-45%, worst day>=-20%
- >=2/3 positive folds; worst fold>-25%
- SEVERE return>50%, PF>1.05
- SUPERSEVERE return>0, PF>1
- no ruin, max open gross<=1.000000001
- max asset contribution<=70%, top10 abs daily concentration<=40%

Additional Phase245 hurdle: **BASE Phase245 total return must exceed BASE passive Clean-4 total return**.

Pass => GROWTH_CORE_CANDIDATE. Failure => REJECT_GROWTH_CORE_NO_RESCUE for this exact market-state rule. No validation/holdout.
