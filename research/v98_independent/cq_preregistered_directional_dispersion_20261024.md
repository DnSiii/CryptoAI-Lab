# V98 Independent CQ — preregistered directional dispersion with compression-breakout recovery (2026-10-24)

## Distinct thesis, no rejected-engine rescue
CQ tests **persistent trend with cross-sectional upside dispersion and volatility-compression recovery**. Its Relative Value is directional BTC-versus-alt relative leadership rather than CO's ETH/BTC mean-reverting ratio, CP's beta residual, CM's downside-beta short, CK's funding-carry spread or CN's cash-relative single-asset rotation. Opportunity requires volatility-adjusted 48h breakout rather than CO volume surprise or CP selloff absorption. No rejected signals, weights, parameter tuning or performance are imported. Only generic V98 physical execution/governor and independent artifact accounting reused.

## Locked seven slots
1. **Growth Core:** every 336h, rank assets by trailing 672h positive log return divided by sqrt(672) times 672h hourly realized volatility. Eligible if 672h and 168h log returns are both positive. Long top eligible 55%, second 45%; single eligible 100%; else cash.
2. **Opportunity:** every 168h, among BNB/SOL, require 48h log return >0.03, latest completed close above preceding 336h maximum completed close (exclude current close), and latest 72h realized volatility > preceding 336h realized volatility. Long candidate with largest 48h return; otherwise cash.
3. **Relative Value:** every 168h, among ETH/BNB/SOL require 336h excess log return over BTC >0.02, asset's 168h return >0, BTC's 336h return >0 and rolling 168h correlation with BTC >0.35. Long best excess asset 50%, short BTC 50%; otherwise cash. Relative momentum spread, **not** ETH/BTC z-score reversion or beta residual selection. No constant short SOL.
4. **Stress/Recovery:** every 168h, if >=2 assets had negative 168h returns, market average 24h return >0 and average 72h hourly volatility < average preceding 336h hourly volatility, long BTC 60% + ETH 40%; else cash. Volatility contraction after systemic weakness, not volatility expansion or a static hedge.
5. **Regime Router:** RISK_ON if >=3 assets have positive 336h log returns and BTC 168h >0; RISK_OFF if >=3 negative 336h and BTC 168h <0; else MIXED.
6. **Dynamic Allocator:** fixed budgets [Growth,Opp,RV,Stress] RISK_ON [1.75,.45,.30,.20], MIXED [1.30,.40,.40,.35], RISK_OFF [.60,.30,.45,.55]. Shared collateral, persistent units, no hidden leverage.
7. **Risk Governor:** unchanged generic CG buffered physical V98 authorization (60% stressed NAV reserve, 40% floor, 18% maintenance, 0.25% participation, staged exits, 81-corner intrabar stress, signed native funding and mark bounds).

## Chronological gates, sealed future
Clean-4 BTC/ETH/BNB/SOL Binance USD-M 1h pinned 2022-12 warmup through 2024-12 only. Never read 2025 holdout, 2026+, XRP, Phase083, or V14/V15/V99 strategies/parameters/performance. Source: pinned native receipt, causal future perturbation, effective active 2023 and 2024 epochs >=4 Growth/Opportunity/Stress, >=8 RV; disclose distinct signal transitions. Fail source => reject with **no** PnL.
If source passes, 20 native physical USD10k training cells (full, core-only, minus each of three sleeves x base/severe x 2 funding orders) independently reproduced on Ubuntu 22.04/24.04. Require 20/20 survival, annual full net log growth >0 both years all cases, CAGR >50% base and >30% severe, severe DD <45%, and each sleeve's full-minus-ablated annual log growth >0 in both years, both costs, both funding orders. No post-result retuning/rescue.
Only after all training gates: USD1m/USD10m, supersevere, independent event-level 81-corner replay, tails/regime/concentration, internal freeze, separate untouched 2025 validation, then external benchmark. No paper/live authorization.

Writes only `research/v98_independent/cq_*` and `.github/workflows/v98-independent-cq-*` on `research/v98-independent-zero`. Frozen V16/V99 and V99 paper/workflows/reports untouched.
