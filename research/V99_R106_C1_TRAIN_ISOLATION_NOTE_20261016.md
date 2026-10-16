# V99 R106 C1 — pre-economic complete-engine freeze, 2026-10-16

C1 is ONE integrated, non-optimized economic mapping, not a rescue of the 100 rejected TRAIN alphas, rejected Donchian breakout, or rejected weekly strength rotation. Prior R106 full/holdout results are contaminated for selection. No use of those diagnostics. No real orders.

## Frozen layers
- Growth: BTCUSDT and ETHUSDT independently. Daily at 00:00 UTC use close(t-1), mean of prior 720 closes, and close(t-1)/close(t-169)-1. Long if above mean and momentum positive; short if below and negative; else cash. Retain position until next daily decision.
- Allocator: each active asset absolute notional min(0.65, 0.55 / annualized volatility of 168 prior hourly log returns); zero/invalid volatility means cash. Gross <=1.30. No cross-asset winner selection.
- Router: BTC 168h lagged momentum: BULL >4%, BEAR <-4%, otherwise SIDEWAYS. BTC 168h lagged annualized volatility: HIGH if >85%, else LOW. In high-vol BULL halve shorts only; in high-vol BEAR halve longs only. Report all 3x2 cells.
- Tail governor: before hour-t execution, use only previously realized portfolio equity. At drawdown <=-20% enter 168-hour cash lock; otherwise at <=-12% halve gross. No intrahour stop. No additional alpha sleeves: idle capital is cash.
- Execution: target decided from completed closes through t-1; fill at open(t); mark at open(t+1); cost on one-sided absolute turnover. Severe cost 0.0007, supersevere 0.0014. These are modeled costs before authenticated position-specific settled funding and actual fills.

## Isolation and gate
Initial TRAIN scored [2021-12-01T00:00Z, 2023-10-01T00:00Z), with earlier warmup. CSV parser must break before reading OHLCV at or after 2023-10-01. Sealed validation [2023-10-01, 2024-01-18); final holdout >=2024-01-18 unopened. No R98/R106 full-history selection.

Five chronological TRAIN folds. For both costs require positive ROI, hourly profit factor >1, positive ROI after removing best day. Require severe >=4/5 positive folds; supersevere >=3/5; supersevere DD >=-35%; >=720 active hours; severe ROI above same-period 100% BTC and 50/50 BTC/ETH modeled-cost proxies. Report worst day, 3x2 regime sample counts, turnover, concentration and cost. These static proxies do not substitute for the V13–V16 benchmark envelope, which remains a later blocking gate. Reproduce bytes and run adversarial causality tests.

FAIL ANY gate -> permanently REJECT C1, NO retune/weight tweak/combination. TRAIN pass only permits code/data freeze then separate validation, never immediate promotion. Native OKX fee tier, settled funding, execution journal, benchmark envelope and untouched final holdout remain separate mandatory gates. Frozen V16/V99, durable paper history and champion untouched. DATA_ONLY/HOLD; NO PROMOTION.

## Pre-economic erratum (2026-10-16; NO historical C1 PnL yet)

Synthetic adversarial testing detected that a naive 168h cash lock would repeatedly re-trigger indefinitely whenever portfolio drawdown remained <=-20% at expiry. This is an implementation defect, not market evidence. Corrected **before the first historical C1 economic run**: keep a one-shot `armed` latch; trigger 168h cash lock only when armed and DD <=-20%, then disarm; after lock expires allow normal risk-scaled exposure (including <=-12% gross haircut), and re-arm only after DD >-12%. Thresholds, cost assumptions, trading signals, sizing, source periods and gates are unchanged. A failed first historical TRAIN evaluation permanently rejects C1 without retuning. See C1 tests and immutable TRAIN artifact; this erratum does not authorize opening validation/holdout.

Integrity-only addition before economic run: the canonical TRAIN input must include at least 721 warmup hours before 2021-12-01 and the last hour 2023-09-30T23:00Z; otherwise fail closed. This checks coverage, not profitability.
