# V98 Independent BV — original frozen native funding, friction and core displacement forensics (2026-10-24)

**BV remains irrevocably REJECTED.** This is a post-rejection diagnostic replay of original BV_full and BV_core_only only; no refit, candidate rescue or holdout use. Original physical training [run 40089713051](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40089713051), independent forensic [run 40090049714](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40090049714).

All four original full/core × base/severe USD10k carried-before-fill paths were re-executed from authenticated pinned Clean-4 Dec2022–Dec2024. Per-asset opening-gap PnL, intrabar PnL, signed 8h native funding, fees, slippage and turnover reconcile exactly with the original receipts. Source 9,144 funding events. 2025 and external benchmarks untouched.

## Original per-year cashflow USD10k (sum across four assets)

| Original path / year | Directional gap+intrabar USD | Native funding USD | Fees+slippage USD | Turnover USD |
|---|---:|---:|---:|---:|
| BV_full base 2023 | +2,478.76 | −84.78 | 367.92 | 367,911.79 |
| BV_full base 2024 | +2,766.20 | −181.34 | 482.24 | 482,247.32 |
| BV_core_only base 2023 | +2,426.41 | −275.75 | 277.76 | 277,753.52 |
| BV_core_only base 2024 | +2,836.83 | −313.24 | 347.74 | 347,742.65 |
| BV_full severe 2023 | +2,245.51 | −76.45 | 1,702.56 | 340,511.98 |
| BV_full severe 2024 | **+1,929.85** | −135.11 | **1,905.78** | 381,156.89 |
| BV_core_only severe 2023 | +2,245.25 | −255.74 | 1,305.25 | 261,050.88 |
| BV_core_only severe 2024 | **+2,309.09** | −226.76 | **1,465.47** | 293,092.57 |

**Mechanistic diagnosis:** in 2024 severe, full path lost about **USD379.24 directional PnL** versus core-only, saved about **USD91.65 native funding**, but paid about **USD440.31 more execution friction**. The full portfolio therefore underperformed the core-only path despite lower funding outflow. At base costs the 2024 directional shortfall was ~USD70.63, funding saved ~USD131.90 and extra friction ~USD134.50. These are path-dependent comparisons, **not** additive alpha estimates: wealth and risk ratchets differ.

Original BV_core_only incurred 21 physical forced ratchets and 57 fill hours; BV_full incurred 30 ratchets and 106 fill hours. Admission-only core priority was insufficient to prevent future risk-governor shrinkage and repeated physical turnover. A genuinely distinct next system should explicitly prioritize core inventory **at each physical hourly risk decision**, close satellites first within available liquidity, and admit incremental satellite risk only with persistent future stress headroom. No impossible instantaneous exits; no re-use of rejected BV signals/parameters. Training validation and future holdout must remain separate.

**Status:** BV rejected, original code and receipt hashes preserved, 2025 holdout sealed, XRP quarantined, 2026+ excluded, V16/V99 Frozen and paper untouched, no real trades.
