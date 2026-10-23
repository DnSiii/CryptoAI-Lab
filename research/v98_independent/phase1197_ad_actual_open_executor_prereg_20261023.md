# V98 Independent Phase1197 — AD self-financing actual-open execution preregistration (2026-10-23)

AD's seven source/decision slots are now individually implemented but **not yet an executable complete engine**. This freezes the actual cash/inventory settlement contract before any official AD historical PnL. No 2025, XRP, contaminated holdout or V14/V15/V99.

At t+1 open, carry prior signed units and cash from the preceding close. Revalue carried inventory at actual opening price **before** any trade; fail on nonpositive opening equity or unexecutable gap. Use Phase1196 81-corner governor and 101-step scalar projection to choose executable new signed units from Phase1195 desired weights. No assumed stop fill, no free inventory teleportation, no borrowing outside signed USD-M exposure constraints.

For each delta units, execution price = actual open * (1 + sign(delta)*0.003 slippage), fee = |delta|*open*{base 0.0007, severe 0.0012, supersevere 0.002}. Self-financing cash -= delta*execution_price + fee. Funding settlement: two frozen orders, **carried-before-fill** or **new-after-fill**. For each signed unit at native settlement t, funding cash = -units*rate*mark, using **mark high when units*rate>0** (adverse payer) and **mark low when units*rate<0** (conservative receiver). No funding at non-events; mark bounds from vendor attestor. Mark after settlement must not be inferred from future data for target selection.

After execution, mark actual high/low/open **81 intrabar corners** and closing NAV. Reject any corner that breaches the same Phase1196 asset/gross/net and 35%-equity-floor constraints; reject nonpositive close NAV. Actual high/low are only used for **post-trade evaluation**, never for the causal sizing decision. Record cash, signed units, turnover, fees, funding, opening gap, NAV, and first failure. A failed cell is rejected, not silently omitted.

The complete AD needs chronological 2023/2024 training, 90-cell capacity/cost/funding-order analysis, independent FIFO PF/payoff/win and 2025 untouched until internal freeze/pass. No rescue of rejected variants.
