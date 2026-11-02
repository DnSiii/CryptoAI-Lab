# V98 Independent — frozen 2025 signed native funding-carry source feasibility (2026-11-01)

**Decision: PASS_SOURCE_DIAGNOSTIC_ONLY; NO EXECUTABLE EDGE ESTABLISHED; NO V98 CHAMPION.** This is a separate economic mechanism from rejected same-hour spot/perpetual basis convergence. It is **not** historical PnL, not a seven-slot candidate, not an optimized trading signal, not validated CAGR and not permission for paper/live execution. Prior rejected engines remain rejected.

## Preregistered evidence and independent replay

- Fixed protocol committed **before code and source evaluation** in commit `fea3d74dc8d8c8763fbb1439fead3363111fc642`, `v98_funding_carry_source_prereg_20261101.md`.
- Full physical source-only GitHub Actions run: [41374492117](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41374492117), commit `8cda07bb3d70f8e581ee44d144d7159b2141a340`, conclusion **SUCCESS** (2026-11-02 01:50 UTC).
- Immutable 30-day artifact `v98-independent-spot-2022-25-masked-bridge-fee-diagnostic-no-pnl`, ID **13109509501**, ZIP digest `sha256:55397d4eed93b5608da3ed304c13c057286779b2bec8ead254ae0dec3d26cb40`; source-event CSV SHA256 `0acaf2a7f23bf9b44e497688f331fc548fba5b3e9414ea6854a0f379510ab951`.
- Reused pinned official NH USD-M 2025 source receipt `sha256:7ce4ec7e2a6980838fa0179729b3cc6da8f131806b03e070590146d6d6ca046b`; per-asset original funding CSV SHA256 checked against receipt. **4,380/4,380** 8-hour source events verified: 1,095 per Clean-4 asset, all 12 fixed UTC months of exposed 2025. No 2026+, XRP, contaminated Phase083, holdout or external benchmark.
- Independent Decimal oracle re-read all 4,380 canonical events, checked exact monthly signed sums, chronology, 48 month counts, all three budget identities and research firewalls. **4/4 deliberate carry receipt/event tamper controls rejected**; existing spot-source oracle also passed its two controls. A second local artifact-level SHA and per-asset/month recomputation matched the GitHub receipt. This is not independent custody of the original exchange HTTP response bytes.

## Fixed monthly source diagnostic, NOT a trading result

Each figure is the **sum of signed exchange funding rates in basis points** for a hypothetical *constant unit-notional short USD-M perpetual*, paired conceptually with a long spot hedge. Positive rate is received by the short, negative is paid. **No basis drift, mark-to-market, execution, borrow, financing, position sizing, fees debited or compounding is simulated.** The budgets of 30/50/70 bps are precommitted illustrative *four-fill* round-trip fee-only comparisons, not verified historical account costs.

| Asset | 2025 sum of signed funding-rate bps (not return) | Positive months / 12 | Months >30 bps | Months >50 bps | Months >70 bps |
| --- | ---: | ---: | ---: | ---: | ---: |
| BTCUSDT | +512.6428 | 12 | 9 | 3 | 2 |
| ETHUSDT | +492.8719 | 12 | 7 | 4 | 2 |
| BNBUSDT | -208.4915 | 5 | 0 | 0 | 0 |
| SOLUSDT | +35.0703 | 7 | 2 | 1 | 0 |
| **All 48 fixed asset-months** | **not a portfolio sum** | **36 positive / 12 negative** | **18/48** | **8/48** | **4/48** |

The precommitted 30-bp nominal-fee hurdle is exceeded in **18/48** asset-months, the 50-bp hurdle in **8/48**, and the 70-bp hurdle in **4/48**. These are *observed historical monthly rate sums*, not 18 independent profitable opportunities, not executable cashflows, and not prospective selection evidence. BNB's fixed short-perp orientation has negative 2025 signed funding sum. **Do not choose BTC/ETH after inspecting this result as a strategy or rescue a rejected architecture.**

## Binding interpretation and critical path

The result shows that *signed native funding carry* is worth distinguishing from naive basis convergence, but does **not** demonstrate an investable edge. The apparent source-level funding advantage can be offset by basis widening between hedge entry/exit, variation margin and liquidation, bid/ask/depth/impact, actual spot+perpetual fees, financing/borrow, collateral constraints and time-varying notional/mark prices. No signed execution ledger, actual PnL or marginal seven-slot contribution was computed. The result is **not** sufficient to create or freeze a V98 champion.

**External evidence needed for exact settlement and executable proof:** (1) 13,524 exchange-origin historical `/fapi/v1/fundingRate` settlement `markPrice` values, with raw pages, request URLs, HTTP Date headers, UTC capture, SHA256 and independent chain of custody (historical direct access previously returned HTTP 451; authorized Binance-origin export with equivalent attestation is acceptable); (2) account-specific historical spot and USD-M fee schedule and fee currency, verified bid/ask/depth/impact at decision/fill timestamps, spot borrow availability/rates if shorting, hedge collateral and liquidation rules. Existing conservative hourly mark envelopes permit exploratory research but not exact settlement attestation.

**Next economically substantive step:** preregister an actual *causal, inventory-matched funding/basis/hedge physical mechanism* with realistic two-leg executions and funding before proposing its integration into a **new complete seven-slot** V98. Any candidate must independently pass chronological exposed training and separate validation, severe/supersevere costs, optional sleeve marginal growth, drawdown/tails and reproducibility, then freeze **before** opening external V14/V15/V99 benchmarks. Future holdout and prospective paper remain locked. No guarantee of returns, no live/paper authorization. All changes confined to `research/v98_independent/`; V16/V99 Frozen, V99 research/paper and other branches untouched.
