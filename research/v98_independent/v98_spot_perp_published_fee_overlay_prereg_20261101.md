# V98 Independent — published regular-user two-leg fee overlay, source-only (2026-11-01)

**Fixed public fee overlay before the 30-bp diagnostic is run; no strategy or PnL selection.** After the original preregistered 8/16/24-bp illustrative four-fill source diagnostic (run 41333061032), verify the current **public** Binance regular-user spot and USDT-margined perpetual schedules separately. The official fee tables available on 2026-11-01 show regular-user spot maker/taker **0.100% / 0.100%** and USD-M USDT futures maker/taker **0.0200% / 0.0500%**. Primary sources:
- https://www.binance.com/en/fee/trading
- https://www.binance.com/en-BH/fee/futureFee

A one-round-trip, equal-notional, four-fill **spot taker + perp taker** scenario has a nominal published fee-only sum `2*10 + 2*5 = 30 bps` of one-leg notional, **before** funding, borrow, spread, impact, financing, slippage, collateral or liquidation. A spot taker + perp maker **conditional** fee-only scenario has `2*10 + 2*2 = 24 bps`; maker fills are not guaranteed. These are **current public indicative regular-user rates**, not authenticated 2025 historical account-specific fees or execution fills. BNB discounts, VIP tiers and pair-specific promotions are deliberately **not assumed**.

Extend the frozen source-only descriptive 2025 basis diagnostic to count asset-hours where absolute contemporaneous spot/perp close basis exceeds **30 bps**, in addition to original 8/16/24 bps. No entry signal, future return, realized PnL, optimal threshold, fee rescue or executable trade is inferred. This conservative 30-bp comparison is a friction viability filter only; a basis magnitude above fees is still not a monetizable convergence or carry edge. The source receipt and independent audit must fail if the 30-bp count exceeds the 24-bp count or the published-fee scenario is mislabeled as historical execution evidence.

**No action on any Frozen, V99, paper, 2026+ price data, Phase083, holdout or XRP.** The 13,524 exact funding settlement mark prices and historical account-specific fee/carry/borrow/liquidity evidence remain outstanding.
