# V98 MC — preregistered disjoint-regime liquidity-reversal portfolio (2026-10-29)

**Immutable pre-result hypothesis.** New seven-slot composed engine. All MB/MA/LZ and earlier rejections remain frozen; MC neither retunes nor transplants rejected signals. Only authenticated Clean-4 BTC/ETH/BNB/SOL Binance USD-M 1h, Dec 2022 warmup and 2023–2024 TRAINING. No 2025+, XRP, Phase083, V14/V15/V99, holdout or paper. All prices observed through completed t; targets fill next open t+1. SHA-pinned official mark 1h signed worst-side funding envelope, not exact funding-tick mark. Base 4/2 bps, severe 10/10, supersevere 15/20; carried-before-fill and new-after-fill both tested.

## Economic mechanism and fixed rules
1. **Growth Core** (336h clock starting t=744): rank positive 504h returns using 168h downside semi-vol denominator 0.06 + 3×hourly downside std. In BULL breadth (>=3 assets with positive 168h return) hold top two at 0.48/0.20 NAV; in MIXED breadth 1–2 hold 0.36/0.12; in BEAR hold zero. No core reallocation from ablated sleeves.
2. **Opportunity Sleeve** (96h clock): only BULL, rank assets with 168h return >0 and 48h return >0, require latest 48h average quote-volume > preceding 120h average, then buy best 48h return at +0.12 NAV for 96h. Do not enter on expiry clock.
3. **Relative-Value Sleeve** (48h clock): only MIXED or BEAR; cross-sectional 48h return spread >0.025, select worst 48h asset long and best 48h asset short, equal +0.065/-0.065 NAV for 48h. This is **liquidity dislocation reversal**, explicitly opposite to MB residual momentum, and in disjoint regimes from Opportunity. No same-clock reentry.
4. **Stress/Recovery Sleeve** (48h clock): only BEAR or MIXED, >=2 negative 168h returns and >=2 positive 24h returns; buy strongest positive 24h recovery +0.10 NAV for 96h. No same-clock reentry.
5. **Regime Router:** BULL if 168h positive breadth >=3, MIXED if 1–2, BEAR if zero. Optional sleeves gated as above, no future regime observation.
6. **Dynamic Allocator:** core reservation first, optional sleeves share remaining gross pro rata if necessary, maximum intended gross 0.88 NAV; no capital redistribution on ablation.
7. **Risk Governor:** causal atomic close-first pretrade, 3% ex-ante funding event reserve, fees/slippage deducted before increases, no intermediate gross >100% NAV, post-funding gross <=93% NAV and positive intrabar worst-side equity. No future mark/rate enters sizing.

## Hard pre-PnL source gate
Independent replay of all three optional entry calendars, zero mismatches/invalid/silent updates, authenticated and synthetic future-mutation tests, max intended gross <=0.88, >=8 entries per optional sleeve in **each** of 2023 and 2024. Failure = terminal SOURCE rejection before PnL, no threshold or sign rescue.

## Hard economic training gate
Five actual hourly books: full, core-only, minus Opportunity, minus RV, minus Stress; three costs × two funding orders = 30 cells. Require base CAGR >50%, severe CAGR >30%, both severe annual returns >0, severe drawdown <45%, base/severe turnover <=USD600,000 per USD10k start, each optional sleeve marginal full-minus-ablation net log growth >0.02 at base and severe, annual marginal >-0.03. Compute PF/payoff/win-rate, positive days, CVaR1%, concentration, tails and all invariants. Do not rescue rejected MC.

If provisional training passes, **freeze MC** before independent all-hour ledger/PnL replay, 81-corner and cross-OS, separate chronological 2025 validation, pristine future holdout and only then external benchmarks. No live execution or validated-return claims prior to gates.
