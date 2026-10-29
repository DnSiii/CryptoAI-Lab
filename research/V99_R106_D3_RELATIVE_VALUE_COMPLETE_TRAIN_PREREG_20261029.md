# V99 R106 D3 — one-shot preregistration: BTC/ETH relative-value mean reversion (2026-10-29, 08:xx BRT)

**Commit this document BEFORE code implementation or any D3 historical PnL. No optimization, retuning, second variants or promotion on synthetic/green CI.**

## Mechanism and distinction
A temporary BTC-vs-ETH relative-price dislocation may mean-revert as common crypto-market beta cancels in a two-perpetual, equal-initial-USD-notional long/short spread. This is **NOT** C1 trend, E1 long-only spot beta, D1 funding carry, D2 within-asset spot/perp basis, I1 options, weekly relative-strength momentum or Donchian. This is a single falsifiable hypothesis, not a grid. If it fails TRAIN, reject permanently without modifying rules.

## Source and sealed boundaries
Original OKX BTC-USDT-SWAP and ETH-USDT-SWAP hourly **open** receipts from the independently verified 636-page four-leg archived TRAIN artifact (Actions 40019588739), verified again by the existing independent raw-page receipt oracle. Exact grid [2021-12-09T00:00:00Z, 2023-10-01T00:00:00Z), 15,864 hours. No validation [2023-10-01,2024-01-18) or holdout >=2024-01-18 access. No same-hour signal use.

## Fixed complete execution rules
At hour t, use only opens through t-1. Define r_i = log(ETH_perp_open_i / BTC_perp_open_i). The previous 720 hourly r samples [t-720,t) define population z=(r_(t-1)-mean)/std, or no signal if std <= 1e-12. At t open, if flat and not in cooldown: z >= +2 => long BTC perp / short ETH perp; z <= -2 => long ETH perp / short BTC perp. Each leg exactly 0.20 of **initial USD equity** notional at the contemporaneous t open (q=+/-0.20/open), fixed base-coin quantity throughout hold. Maximum gross entry exposure 0.40 initial USD equity, no pyramiding, no simultaneous spreads, no leverage scaling. Exit if |lagged z|<=0.25, age >=168 hours, or last TRAIN hour. On any exit, enforce a fixed 168-hour cooldown (including after terminal), preventing same-hour re-entry. No price-based stop or posthoc governor. If any NAV <=0 or nonfinite, fail closed. Flatten at last TRAIN open.

Hourly accounting: mark previous open to current open on each held signed perp quantity; then debit scenario fees for every entry/exit at current opens, 0.0007 severe or 0.0014 supersevere **per USD notional per leg per side**. Both scenarios share identical signals, positions and trade schedule, with scenario-specific NAV. Funding cash flows are **not** treated as zero or authenticated: pre-funding hypothetical metrics only. Real funding, margin/liquidation, fee tier, actual fills/slippage and order-book depth remain missing, hence no economic certification or promotion.

## Prespecified tests and decision gates
Five chronological fold boundaries (UTC): 2021-12-09 00:00; 2022-04-20 04:00; 2022-08-30 09:00; 2023-01-09 14:00; 2023-05-21 19:00; 2023-10-01 00:00. Six descriptive regimes: BTC lagged 168h price move >+5% BULL, <-5% BEAR, else SIDEWAYS; lagged 168h BTC hourly-return population std >=1% HIGH_VOL else LOW_VOL. At start of history with insufficient regime lookback, SIDEWAYS_LOW_VOL. Regime is descriptive, not used for decisions.

Both severe and supersevere must pass ALL: total ROI >0, severe >=4/5 positive folds and supersevere >=3/5, profit factor >1, maximum DD >=-35%, ROI after removing best hour >0, top 1% of positive hourly gains <=40% of total gains, worst 1% losses <=50% of total losses, ROI above BOTH cash (0%) and fixed 50/50 BTC/ETH spot buy-and-hold benchmark, all 6 regimes present, at least one completed spread. Independently recompute every hourly signal, position, mark, fee, NAV, fold, tail, benchmark and gate directly from original source. Missing data, oracle mismatch, or any failed gate => REJECT_D3_NUMERIC_TRAIN_PERMANENT_NO_RETUNE or SOURCE_BLOCKED; no validation unlock. If numeric pass but native evidence missing => D3_NUMERIC_ONLY_HOLD, no freeze/promotion.

## Immutable safety
Never modify V16/V99 Frozen, legacy champion, paper/results or historical rejection files. No orders, no paper PnL, no claimed exchange-certified profits. This one-shot D3 hypothesis is not an invitation to test multiple posthoc variations.
