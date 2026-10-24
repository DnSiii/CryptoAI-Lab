# V98 Independent BT — frozen post-rejection physical cashflow and core-displacement forensics (2026-10-24)

**BT remains irrevocably REJECTED.** This is a diagnostic reconstruction of the original unmodified BT_full and BT_core_only; no rerun with changed signals/thresholds, no rescue, no new candidate. Original training: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40088242975 . Independent post-rejection attribution: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40088584060 . A first forensic attempt failed before analysis because a namespace substitution changed `BNBUSDT` to `BTBUSDT`; this was corrected mechanically, without altering the original economic engine.

## Original USD10k, base, carried-before-fill: per-year accounting

| Original path / year | Directional gap + intrabar PnL USD | Native funding USD | Fees+slippage USD |
|---|---:|---:|---:|
| BT_full 2023 | **−1,766.11** | −77.28 | 427.40 |
| BT_core_only 2023 | **+721.15** | −121.60 | 316.53 |
| BT_full 2024 | **+4,381.66** | −50.83 | 595.66 |
| BT_core_only 2024 | **+14,194.19** | −686.21 | 470.38 |

Original full 2023 directional PnL by asset: BNB −878.48, BTC −183.62, ETH −176.30, SOL −527.71 USD. Core-only 2023: BNB −284.34, BTC +253.64, ETH −167.99, SOL +919.83. Original full 2024: BNB +1,570.53, BTC +1,301.07, ETH +959.82, SOL +550.25; core-only 2024: BNB +3,288.90, BTC +5,209.58, ETH +2,890.29, SOL +2,805.43.

**Measured obstacle:** in 2024, full-path directional PnL was approximately **US$9,812.53 below core-only**, while funding outflow was ~US$635.38 lower and execution friction ~US$125.28 higher. Thus *lost directional compounding / inventory displacement*, not merely explicit funding or fees, is the dominant economic failure. Path-dependent comparisons are NOT additive per-sleeve alpha estimates; the full and ablated portfolios have different wealth and risk ratchets.

Both full/core original source/settlement paths were independently re-executed under base and severe; per-asset native funding, opening-gap PnL, intrabar PnL, turnover, fees and slippage reconcile exactly to original receipts. Clean-4 2022-2024 only, 9,144 native funding events. No 2025, 2026+, XRP or external V14/V15/V99. V16/V99 Frozen and paper untouched.

**Next genuinely distinct architecture hypothesis:** preserve the persistent growth core with an *explicit protected core inventory/risk budget*; permit satellite modules only when ex-ante incremental stress headroom is available, and make them prove positive marginal net log growth without mechanically replacing profitable core units. Do not modify or resurrect BT.
