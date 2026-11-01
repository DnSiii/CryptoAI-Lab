# V98 Independent — frozen masked spot bridge + published-fee feasibility finding (2026-11-01)

**Decision: PASS_SOURCE_BRIDGE; FAIL_TO_ESTABLISH_TWO_LEG_EXECUTABLE_EDGE. Not an approved strategy, not PnL.** Preregistered source bridge in commit `73caf268ce4d5bdf2338e07cb13aac8fa1631ba7` before implementation; original illustrative diagnostic passed in [run 41333061032](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41333061032). The separate current published-fee overlay was registered in commit `bbe977fb4b19f09ca762e36f519056fcad80aa07` **before** the 30-bp computation; final [run 41333160658](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41333160658) succeeded with independent audit and two tamper controls rejected.

## Authenticated full-history source bridge
Reused immutable GitHub Actions artifacts from HQ masked official spot run 40441987477 (100 original provider-verified 2022–2024 archives), 2025 official spot run 41328347003 (48 original provider-verified 2025 archives), and 2025 USD-M perpetual run 41076438477 (144 official provider-verified archives). No redundant vendor download, data repair, interpolation, forward fill or lookahead.

- Four assets BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT; Dec-2022 to Dec-2025, **27,048 UTC hours each = 108,192 asset-hours**.
- **108,188 observed spot bars; 108,184 full-hour eligible bars; four 2023-03-24 12:00 UTC publisher early-close partial bars and four 13:00 UTC missing bars explicitly masked.** All 2025 35,040 asset-hours observed and complete. Strictly rejected older full-grid spot source remains rejected.
- Canonical bridge SHA256 `c40f6e751690a6faf98d8fc25f0fc2111d6723828a39871b07a3f81869bccfed`. Independent read-only oracle reproduced all 108,192 calendar cells and rejected 2/2 receipt tampering attempts. All receipts say **no system PnL, no holdout, no live**.

## Economic feasibility: 2025 observed closes, descriptive only
Source-only raw basis = `abs(perpetual 1h close / spot 1h close - 1)`, not an executable bid/ask arbitrage and not a trade entry signal. Each asset has 8,760 exposed 2025 training hours. The following are **hour counts**, not independent opportunities or profitable trades:

| Asset | Median absolute basis (bps) | Hours >8 bps | Hours >16 bps | Hours >24 bps | Hours >30 bps |
|---|---:|---:|---:|---:|---:|
| BTCUSDT | 4.428442 | 4 | 1 | 0 | **0** |
| ETHUSDT | 4.426165 | 17 | 5 | 1 | **0** |
| BNBUSDT | 4.466134 | 765 | 28 | 5 | **1** |
| SOLUSDT | 5.027336 | 311 | 32 | 13 | **5** |
| **Total** | — | **1,097** | **66** | **19** | **6 / 35,040 (0.0171%)** |

Current public Binance regular-user **spot taker 10 bps** per fill and **USDT perpetual taker 5 bps** per fill, so an equal-notional four-fill spot+perp taker round trip incurs **30 bps** of *nominal fee-only* cost: spot open/close 20 bps + perp open/close 10 bps. Official current schedule references: https://www.binance.com/en/fee/trading and https://www.binance.com/en-BH/fee/futureFee. This is **not** verified account-specific or 2025 historical fees. Maker fills, discounts and promotions are not assumed; spread, depth, borrow, funding, slippage, capital efficiency and execution timing remain unknown. Even 6 hours above 30 bps are **not** evidence of monetizable convergence, because future basis movement and fill feasibility were not tested.

**Decision for research allocation:** do not promote naive same-hour basis convergence as V98 Growth Core on this evidence; do not rescue it by selecting fee tiers, sign or threshold after the result. A distinct funding-carry or dynamic hedging mechanism could still be studied only with preregistered signed funding, borrowing/collateral, full execution and independent physical cash ledger. Prior rejected HW and other historical strategies remain rejected. This diagnostic neither passes nor rejects an untested seven-slot candidate.

## Remaining delivery gates
1. **Exact funding event marks:** 13,524 exchange-origin `markPrice` at settlement remain missing due prior HTTP 451. Required authorized raw `/fapi/v1/fundingRate` pages with original response bytes, URLs, UTC retrieval timestamps, HTTP Date headers, per-page SHA256 and independently verified custody; equivalent authorized exchange-origin export is alternative. Current 1h envelope is conservative proxy, not exact mark.
2. **Executable costs:** account-specific spot and USD-M fees historically applicable, funding settlement and fee currency, actual bid/ask/depth/market impact, spot short/borrow availability and rates where needed, capital/hedge and liquidation accounting.
3. **New seven-slot complete V98:** preregister distinct growth economics; causal full 2022–2025 exposed training, chronological separate validation, severe/supersevere costs, independent accounting, frozen candidate and untouched future holdout; only then benchmark against external engines. No 2026+ accessed for training and Phase083 remains ineligible.

**Scope verification:** comparison of pre-cycle commit `2f3a7937a179c59223e87c5d288e1ddc6058373c` with overlay commit `0a54604d62277190b2edba55f295a3e2b137b347` showed only five V98 Independent namespaced source, oracle, preregistration and workflow files. No V16 Frozen, V99, other branches or paper modified. No operation real authorized.
