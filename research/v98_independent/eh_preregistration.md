# V98 Independent EH — preregistered cross-sectional orthogonality allocator (2026-10-25)

**Before any EH source/economic result.** EH tests a genuinely different complete seven-slot hypothesis: maximize native net trend growth with three complementary *cross-sectional* sources, allocating satellites according to instantaneous signed exposure orthogonality to the core, not the EG virtual-profit gate or any previously rejected candidate's parameter/sign/window/conditional winner. Reuse only authenticated Clean-4 source, physical V98 collateral/settlement and independent receipt audit infrastructure.

Universe: BTC/ETH/BNB/SOL Binance USD-M 1h; Dec-2022 exactly 744h warmup, full Jan-2023–Dec-2024 training; no 2025+ reads, XRP, Phase083, V14/V15/V99 signals/parameters/benchmarks, Frozen, paper or live orders.

1. **Growth Core** every 120h: long 25% equal-weight floor plus 75% positive 480h native funding-adjusted log momentum / 480h downside semivol, only assets with positive 120h price trend; equal-weight fallback.
2. **Opportunity** every 24h: strongest ETH/BNB/SOL by 120h price trend if 6h price trend positive, current 24h candle close-location value >0.60, and mean last 24h quote volume > prior 120h mean. Long selected asset, else flat.
3. **Relative Value** every 24h: short the most volatile ETH/BNB/SOL and long the least volatile ETH/BNB/SOL, using trailing 240h realized volatility, only when volatility ratio >1.35 and least volatile alt outperformed most volatile alt over 24h. 0.5/0.5 gross neutral.
4. **Stress/Recovery** every 24h: when BTC outperformed the weakest ETH/BNB/SOL over trailing 48h by >1.0% and equal-weight market trailing 48h trend negative, long BTC and short that alt 0.5/0.5. Continuous relative-defense selection, not EG crisis-only 72h/semivol trigger.
5. **Regime Router:** TREND if equal-weight market 120h return >0 and >=3 positive 480h native trends; RISK_OFF if market 48h return <-2% and <=1 positive 480h net trend; otherwise MIXED.
6. **Dynamic Allocator:** core notional budgets TREND/MIXED/RISK_OFF (3.25/2.65/1.60). Satellite nominal budgets TREND (.16,.12,.12), MIXED (.15,.18,.20), RISK_OFF (.08,.18,.30). Each satellite receives multiplier `max(0.35, 1 - abs(dot(sleeve,core)) / (norm(sleeve)*norm(core)+1e-12))` and common volatility multiplier clipped [0.5,1.2] from 0.0075 / prior 240h market hourly vol. No realized-return gating, no retroactive switching.
7. **Risk Governor:** unchanged 81-corner shared collateral, staged 24h exit, 60% stressed post-fill NAV, signed native funding, two funding orderings, base/severe/supersevere costs, completed-close signal t -> next actual open t+1, no hidden leverage.

**Pre-PnL source gate:** deterministic future mutation leaves all earlier signals/updates/budgets unchanged; each year 2023/2024 at least (4,8,12,8) active updates for Growth/Opportunity/RV/Stress. Fail => permanent source rejection, no PnL.

**Economic gate:** 5 physical paths (core/full/leave each satellite out) × 3 costs × 2 funding orderings = 30 cells on USD10k, reproduced on Ubuntu22.04/24.04. 30/30 survival, independent artifact-only audit, full net log growth positive both years base/severe both orders, strictly positive physical marginal net log growth for each satellite in both years base/severe both orders, base CAGR >50%, severe CAGR >30%, severe drawdown <45%, turnover <=USD600k. Report costs/funding, PF, payoff, win rate, positive days, concentration, tail losses, reproducibility. Passing training alone never unlocks 2025 holdout or external benchmarks until candidate freeze; never live trade.

**No rescue:** no sign, window, threshold, gross or budget changes after seeing EH results. Rejected experiments stay rejected.
