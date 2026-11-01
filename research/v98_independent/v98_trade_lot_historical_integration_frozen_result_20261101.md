# V98 — historical trade-level PF/payoff/win accounting integration (2026-11-01)

**PASS_HISTORICAL_TRADE_METRIC_INTEGRATION_ONLY_NOT_ENGINE.** This is a measurement-infrastructure result on the **permanently rejected PU** full-book historical ledger, **not a PU rescue, strategy approval, independent future validation, execution attestation or paper result**. PU's binding economic rejection remains unchanged.

- Binding pre-run contract: `v98_trade_lot_historical_integration_prereg_20261101.md`, committed at `ac98dfa51585543ce53267d8c13017b50ffb94b1` before implementation and before this historical metric run.
- Historical runner and immutable GitHub Actions receipt: [run 41363925260](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41363925260), commit `c4de803b7e5870c92ffffb017796cd2c6601c4a8`, six-cell artifact ID `13106690934`.
- Same Clean-4 official pinned source artifacts, 27,048 source hours Dec-2022–Dec-2025, 26,303 simulated cash-ledger hours per scenario, exposed 2023–2025 TRAINING only. Exactly **6/6 complete physical ledgers**, all hourly independent cash and fee/slippage/funding checks passed, and independent output/no-promotion assertions passed.

| Frozen rejected PU full book | Closed net-asset episodes | Closed PF | Closed payoff | Closed win rate | NAV reconciliation absolute error |
| --- | ---: | ---: | ---: | ---: | ---: |
| Base, carried-before-fill | 143 | 1.157358 | 1.601012 | 41.9580% | 1.30e-10 USD |
| Base, new-after-fill | 143 | 1.157379 | 1.601041 | 41.9580% | 9.37e-11 USD |
| Severe, carried-before-fill | 143 | 1.095735 | 1.702303 | 39.1608% | 2.98e-10 USD |
| Severe, new-after-fill | 143 | 1.095753 | 1.702330 | 39.1608% | 3.29e-10 USD |
| Supersevere, carried-before-fill | 143 | 1.037199 | 1.659518 | 38.4615% | 1.75e-11 USD |
| Supersevere, new-after-fill | 143 | 1.037214 | 1.659542 | 38.4615% | 9.46e-11 USD |

**Interpretation:** PF, payoff and win rate are **net asset-position episodes**, not individual exchange fills, virtual sleeves, or hourly winning NAV observations. Episode PnL includes partial closes, sign flips, modeled fee/slippage and signed conservative funding, and excludes unrealized open episodes from closed-trade PF. They are measured on the rejected strategy solely to establish that future candidates can be evaluated with a historical metric rather than a synthetic-only unit test. No ex-post PU parameter tuning, threshold adjustment, or reclassification is allowed.

**Still not proven:** exact 13,524 exchange funding-event `markPrice` values, account-specific historical fee schedule, executable bid/ask/depth/impact, independent chronological future validation, untouched holdout, and prospective paper. Exact native marks require authorized raw `/fapi/v1/fundingRate` pages with URL, response bytes, HTTP Date, UTC capture, SHA256 and custody verification, or an equivalent independently attested exchange-origin export; historical API returned HTTP 451. Conservative hourly bounds remain exploratory proxies. These missing items prevent final V98 delivery even if a future seven-slot candidate passes exposed training.

**Decision:** historical trade-level metric infrastructure now passes a six-cell real historical-ledger integration. **No complete V98 approved**. Next economic work must be a genuinely distinct preregistered seven-slot candidate with robust positive net growth and marginal contributions, not a revival of PU. No V14/V15/V99 benchmark, 2026+ training, XRP, Phase083, holdout, Frozen or paper touched.
