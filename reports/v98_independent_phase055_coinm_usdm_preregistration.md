# V98 Independent Phase055 — COIN-M ↔ USD-M collateral dislocation

Status: PREREGISTERED BEFORE ANY PHASE055 PnL/RETURN COMPUTATION.

## Economic hypothesis
For the same underlying, temporary relative-price dislocations between Binance COIN-M inverse perpetual and USD-M linear perpetual contracts should mean-revert after removing the cross-sectional common component. A relatively cheap COIN-M contract is held long against the same underlying USD-M contract short; a relatively rich COIN-M contract is held short against USD-M long. This is a collateral/contract-segmentation relative-value hypothesis, not a directional crypto hypothesis.

## Frozen design
- Training only: 2023-01-01 through 2025-12-31 UTC.
- Assets fixed before PnL: BTC, ETH, BNB, XRP, SOL.
- Contracts: BTCUSD_PERP/BTCUSDT, ETHUSD_PERP/ETHUSDT, BNBUSD_PERP/BNBUSDT, XRPUSD_PERP/XRPUSDT, SOLUSD_PERP/SOLUSDT.
- Input bars: public Binance 1h monthly COIN-M and USD-M perpetual klines.
- Relative basis: `log(COIN-M close / USD-M close)`.
- Information set: 24h rolling mean basis using data only through t-1.
- Signal: negative lagged 24h mean basis, cross-sectionally demeaned/ranked; positive means long COIN-M / short USD-M.
- Rebalance cadence: fixed 8h.
- Portfolio gross across both legs: 0.75 total; each spread allocation contributes two legs.
- No threshold, symbol subset, sign, window, cadence, gross, or regime search.
- Returns: next-hour COIN-M return minus USD-M return, with positions shifted one additional bar.
- Funding: public funding-rate archives for BOTH COIN-M and USD-M; long pays positive funding and short receives it.
- Trading costs per traded leg: base 7 bps, severe 12 bps, supersevere 20 bps; turnover counts both legs.

## Frozen training gate
Promote only if ALL structural requirements hold: base return > 0; base daily PF >= 1.15; severe return > 0; supersevere daily PF >= 1.00; at least 2/3 chronological calendar-year folds positive. Report max drawdown, payoff, win rate, positive days, regimes, concentration/tails/turnover and coverage regardless of pass/fail. No rescue after failure.

## Isolation
Phase055 may not request validation or final-holdout data. V99 evidence/state is forbidden. Validation remains closed unless this frozen training gate passes; final holdout remains untouched until a later formally frozen candidate passes training and validation.