# V99 I1 — fixed causal 30d variance-premium entry signal (2026-10-26, preregistered before code)

**SOURCE/RESEARCH ONLY — NO PROMOTION.** This is the missing t-1 decision bridge for the already distinct I1 options architecture, **not** an options economic backtest, fill or return. Never reuse the structural forward 720h realized-variance outcome as a trading input.

## Immutable data and clock
- TRAIN only [2021-12-09, 2023-10-01) UTC, original five chronological R106 folds; 94 Mondays 00:00 UTC, of which exactly 91 can mature inside TRAIN (3 right-censored excluded). BTC and ETH both evaluated for every eligible Monday; no validation or holdout reads.
- Reuse original independently checked first-party OKX BTC/ETH hourly TRAIN opens from Actions 40019588739 and Deribit 30-day DVOL from Actions 40072202459; both source loaders already hash-check original receipts. DVOL is a **closed** candle available before decision, never a contemporaneous or future DVOL observation.
- At Monday decision index i, use exactly 720 trailing **already observed** hourly open-to-open log returns `log(P[j]/P[j-1])` for j=i-720,...,i-1; both price observations precede decision. If i<721, signal is `NO_30D_HISTORY` (never backfill or shorten the window). Use the original asset's spot series, not BTC as proxy for ETH.
- `lagged_rv_30d = sum(log_returns**2)`; `implied_var_30d=(DVOL_percent/100)**2 * (30/365)`. Signal is `POSITIVE_EX_ANTE_PREMIUM` iff implied_var_30d > lagged_rv_30d; otherwise `NO_PREMIUM`. **Zero tuned threshold**, no forward-return filter, no search over windows.
- Preserve every week, including no-trade signals. Publish only source-time decision counts, by fold and asset, never ROI. Independently recompute each signal from original source; falsify one reported value and prove that changing future price P[i+1] does not alter the decision at i.

## Economic completion gates (unchanged)
- This is only the causal signal component of one preregistered I1 short-volatility defined-spread architecture. It does not authorize selecting strikes, pricing fills, trading, a NAV, or comparing to a benchmark.
- Any complete strategy must bind the signal to original 2021–2023 BTC/ETH options **entry and every holding-period mark/exit** two-sided books and sizes, native coin contract units, original index/TWAP, historical fee tier and delivery fees, collateral/margin/liquidation and executable costs. Same gross trade intents across severe and supersevere scenarios; no scenario-specific alpha selection. Account for five chronological folds, 3x2 regimes, tails, max drawdown and benchmark envelope, with an independent economic journal oracle. All future data remains sealed.
- A positive causal signal is **not** evidence of tradeable option premium or profitability. Existing C1 and all rejected strategies stay rejected. No changes to Frozen, paper/results, legacy champion, public performance, or orders.

**Prerequisite for actual economics:** original authenticated complete lifecycle options archive and native historical terms, as documented in issue #19. This signal uses existing genuine historical spot/DVOL bytes and is not a substitute for those missing receipts.
