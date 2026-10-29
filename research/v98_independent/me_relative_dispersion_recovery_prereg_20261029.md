# V98 ME — preregistered asymmetric cross-sectional drawdown dispersion portfolio (2026-10-29)

**FROZEN BEFORE IMPLEMENTATION / RESULTS.** New complete seven-slot engine, not a retune of rejected MD (funding carry), MC (48h contrarian RV), MB (168h momentum RV), MA, or other rejected systems. Independent of V14/V15/V99. Training-only Clean-4 BTC/ETH/BNB/SOL Binance USD-M 1h, 2022-12 warmup, 2023–2024 training. No 2025+, XRP, contaminated Phase083, paper, or Frozen. Signal at completed hour t, next open t+1; native signed funding, official worst-side 1h mark envelope, two fill/funding orderings; base 4/2 bps, severe 10/10 bps, supersevere 15/20 bps.

## Mechanistic thesis — convex asymmetric dispersion in downtrends, not funding or 168h rank momentum
1. **Growth Core:** every 336h from t=744, compute 336h log return and 168h downside semivol; choose highest positive 336h log return divided by (0.06 + 4×semivol) and second positive; BULL (>=3 positive 168h assets): +0.52/+0.22 NAV; MIXED (1–2): +0.40/+0.12; BEAR (zero): cash. No negative-score longs.
2. **Opportunity:** every 168h, BULL/MIXED, at least two assets positive over 168h; buy +0.13 NAV of asset with highest positive 24h return among those with 168h positive return and close above highest completed prior 72h close. Hold 168h; no same-clock reentry.
3. **Relative Value:** every 168h, *only if cross-sectional downside dispersion is wide*: rank assets by 72h downside semivol / 168h upside semivol (each stabilized by 0.002); long asset with smallest ratio, short asset with largest ratio, +0.065/-0.065 NAV, only when spread >0.15. Hold 336h. This is downside/upside shock **asymmetry**, not 48h contrarian returns, 168h price momentum, or funding carry. It can be wrong and must contribute net marginally.
4. **Stress/Recovery:** every 168h, if at least two assets have negative 168h return but at least one has positive 24h return, buy +0.10 NAV of strongest positive 24h asset for 168h; no same-clock reentry.
5. **Regime Router:** BULL if >=3 positive 168h, MIXED if 1–2, BEAR otherwise. Core and Opportunity gated, RV and Stress independently allowed.
6. **Dynamic Allocator:** core priority, optional sleeves scaled together to keep total intended gross <=0.88 NAV, ablated capital stays cash.
7. **Risk Governor:** pre-existing causal close-first atomic planner (not a trading signal), pre-trade cash/cost/funding reserve, no future funding mark/rate for sizing, intermediate gross <=100% NAV, post-funding gross <=93%, positive worst intrabar equity.

## Pre-PnL source-only gate
Independent calendar replay for 3 sleeves, zero mismatches, zero invalid or silent updates, synthetic and authenticated future mutation, intended gross <=0.88 NAV, >=8 actual entries per optional sleeve **each** of 2023 and 2024. Any failure = permanent source rejection; no threshold/sign/window rescue.

## Physical economic gate
Five books (full, core-only, minus each sleeve) × three costs × two signed funding orderings = 30 actual 17,543-hour physical simulations. Full base CAGR >50%, severe >30%, severe annual 2023/2024 returns positive, severe max DD <45%, base/severe turnover <= USD600,000 per initial USD10k, each optional sleeve marginal net log growth >0.02 in base/severe and annual marginal >=-0.03. Reconcile every cell, costs, signed funding, concentration, tails, PF, payoff, win rate, positive days. Reject with exit code 2 for economic failure; never claim a failed CI means a technical failure.

If training passes, freeze engine before independent all-hour ledger oracle, cross-environment reproducibility, stress corners, separate chronological 2025 validation and untouched future holdout. Benchmarks only after internal freeze and validation. No real trading authorization.
