# V99 R106 S2 — one-shot joint-crypto capitulation/rebound spot engine (preregistered 2026-10-29 23:xx BRT)

**EX ANTE: SINGLE DISTINCT ECONOMIC HYPOTHESIS / NO PARAMETER SEARCH / NO RETUNE.** This is not C1 trend, weekly cross-sectional momentum, Donchian breakout, or S1 BTC-vs-ETH laggard mean reversion. Rejected architectures remain rejected. No order execution, no promotion, no validation/holdout/paper/Frozen changes.

## Economic mechanism and data
A synchronized BTC+ETH selloff followed by short-term stabilization can reflect forced deleveraging and temporary liquidity pressure; a **long-only joint rebound** may follow. This is a hypothesis, not an established edge. Use ONLY previously archived first-party OKX BTC-USDT and ETH-USDT hourly **opens** over TRAIN [2021-12-09,2023-10-01), 15,864 observations per leg, source artifact from GitHub Actions 40019588739. Independently verify original four-leg source receipts and exact time grid. Spot only; no shorting, derivatives, leverage, funding, or borrowing. Historical opens are **not historical fills**.

## Fixed t-1 signal and portfolio
- UTC 00:00 decision at hour t, using only opens at or before t-1, warmup 720 hours.
- 24h returns: BTC open[t-1]/open[t-25]-1, ETH similarly. Six-hour recovery: open[t-1]/open[t-7]-1.
- **Fresh event** if both 24h returns <= -0.06 AND both six-hour returns >= +0.01. This is synchronized selloff/rebound, not relative cross-asset mispricing.
- At a fresh event while in cash: enter **35% BTC spot + 35% ETH spot + 30% cash**, hold for **48 hours**, evaluated at subsequent daily decisions. No pyramiding or new entry while a position is open. At expiration exit to cash; no overlapping holds. At every daily decision during hold, early exit to cash if BTC OR ETH trailing 6h return <= -0.05 (causal risk stop); no intraday stop assumption.
- Event entry is evaluated before any exit only when flat; after an exit, no same-hour re-entry. Terminal liquidation on final TRAIN open; modeled turnover fees on all entries/exits. No dynamic drawdown governor, calendar optimization, or discretionary asset switching.
- Full self-financing cash + BTC/ETH units, all hourly marks at original opens; modeled one-way fee+slippage severe 25bps, supersevere 60bps of traded notional. No account-native tier or executable depth evidence; no exchange-certified PnL. Independent oracle must reconstruct decisions, units, cash, fees and hourly NAV from original sources without importing strategy execution code.

## Fixed evaluation and immutable boundaries
- Five chronological folds with UTC boundaries 2021-12-09 00:00, 2022-04-20 04:00, 2022-08-30 09:00, 2023-01-09 14:00, 2023-05-21 19:00, 2023-10-01 00:00. TRAIN only. Validation [2023-10-01,2024-01-18) sealed; final holdout >=2024-01-18 sealed. Never use old contaminated R106 runner.
- Regime reporting: trailing BTC 720h return >+5% bull, <-5% bear, else sideways; BTC 72-hour daily realized sigma >=4% high, else low. Both at t-1; 3x2 regimes with exact hourly attribution.
- Same fixed passive envelope: cash, BTC, ETH, BTC/ETH 50/50 spot buy-and-hold over post-warmup period with matching entry/exit severe fees.
- Gates **ALL**: severe and supersevere net ROI >0; >=4/5 positive folds in both; worst fold >=-5% in both; max DD >=-25% in both; severe ROI > strongest passive benchmark; >=4/6 regimes with >=48 active classified hours positive; remove best single day and remain severe net positive; complete original source and independent per-hour accounting. Native fee tier and actual fill/depth provenance mandatory for any promotion.
- Any failed economic gate: **S2 PERMANENTLY REJECTED, NO RETUNE**. All modeled gates pass but native provenance absent: **MODEL-ONLY SOURCE HOLD, NO PROMOTION**. No performance claims before actual GitHub Actions execution and independent verification. Frozen, champion, paper/results, and order interfaces untouched.
