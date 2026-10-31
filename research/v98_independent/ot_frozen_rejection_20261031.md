# V98 Independent OT — permanently rejected full-history economic experiment (2026-10-31)

**FINAL OT DECISION: REJECT_OT_TRAINING. NOT A V98 CHAMPION.** OT is frozen; do not change its sign, window, weights, thresholds, fee assumptions, 2025 treatment, or gates to rescue it. No external V14/V15/V99 benchmark inspection, 2026+ training, Phase083 holdout, XRP, Frozen or paper/live mutation.

## Preregistration and immutable evidence

- Pre-economic hypothesis committed at `5fb84b362cb2abd454a53c528d6f1b86af76c789`, deterministic governor clarification frozen at `8cf50d5b36a844f24fb4c49b3921db14e73f8979` **before first PnL**.
- Original economic execution: [GitHub Actions 41231130976](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41231130976); full independent replay: [GitHub Actions 41231243110](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41231243110). The first workflow's green source-only status is **not an OT approval**. The second deliberately exits failure because the binding OT economic gates reject the system, not because its physical cells failed.
- Frozen 30-cell signed physical and independent oracle receipt: `ot_full_training_frozen_result_20261031.json`. The independent oracle was added after the initial rejection **without changing signals, execution or economics**; second execution reproduces the original results.

## Historical scope and physical results

Authenticated Clean-4 Binance USD-M BTCUSDT, ETHUSDT, BNBUSDT, SOLUSDT; 2022-12 warmup; **2023-2025 exploratory/training only**, not prospective validation. 27,048 source hours, 13,524 signed native funding-rate events, 26,303 settled physical hours, 157 weekly decisions. Worst-side conservative official hourly mark envelopes, **not exact event `markPrice`**. 2025 is previously exposed and cannot be called independent holdout.

| Carried-before-fill full system | CAGR (2023-25) | Max DD | USD gross turnover | Native-rate signed funding cash | 2023 / 2024 / 2025 |
|---|---:|---:|---:|---:|---|
| Base (4bps fee, 2bps slip) | **+27.6329%** | -35.2623% | 1,138,948.99 | -1,046.16 | +49.8742% / +2.0348% / +35.9834% |
| Severe (10bps/10bps) | **+22.8462%** | -37.6805% | 1,067,791.60 | -997.51 | +44.4526% / **-2.1628%** / +31.1950% |
| Supersevere (15bps/20bps) | **+17.9063%** | -40.1769% | 997,459.64 | -948.79 | +38.8502% / -6.4784% / +26.2412% |

**30/30 physical cells completed** (full, core-only, three sleeve ablations x 3 tiers x 2 funding orders). Base 2023-25 final hypothetical equity USD20,795.09 from USD10k, fees USD455.58, slippage USD227.79. 559/1096 positive daily observations; daily 1% CVaR -5.9983%; hourly NAV-change PF 1.02527, payoff 0.99657, win-rate 50.7099% (**not trade-level PF**). Maximum single-asset gross concentration 100%; 157 net fill events; no forced safety fills. This is historical modeled performance, not realized or forward-validated PnL.

## Binding economic rejection — 22 independently reconstructed failures

All three cost tiers physically settled, but the frozen base CAGR >80%, severe CAGR >60%, base/severe turnover <=USD1m, positive severe annual returns and positive sleeve marginal-growth gates failed. Across the two funding settlement orders, **22 economic failures**: four CAGR, four turnover, two severe annual, twelve sleeve marginal. Base marginal complete-system log growth: Opportunity **0.000000**, Relative Value **+0.005852**, Stress/Recovery **-0.008100**; severe: Opportunity **0.000000**, Relative Value **+0.005648**, Stress/Recovery **-0.008740**. Each was below the preregistered >0.02 gate. The core-only base CAGR +27.729% exceeds the full +27.633%; the optional system did not deliver robust positive marginal wealth. This cannot be cosmetically repaired.

## Independent integrity and limitations

- Independent signal and allocation oracle: **157/157 weekly decisions x five books**, zero mismatches, maximum absolute weight error 0.
- Independent cash-identity audit: **26,303/26,303 hours**, zero mismatches, maximum error ~3.64e-12 USD.
- Independently reconstructed net fills, fees, slippage and conservative signed funding: **26,303 hours, 3,287 funding hours, 157 net fill events**, zero discrepancies; maximum error ~1.78e-15 USD.
- Separate independent recomputation of all 22 binding economic gate failures matched the original decision exactly. Neither arithmetic reconciliation nor historical 2025 inclusion establishes out-of-sample predictive validity.
- **Exact-native funding remains blocked:** to attest full 2022-25 funding cash requires 13,524 official event `markPrice` values with provenance: 9,144 (2022-24, four x 2,286) plus 4,380 (2025, four x 1,095), each matched to the already pinned signed native rates. Required original Binance USD-M `/fapi/v1/fundingRate` pages, timestamps, headers, raw-body SHA256 and independent source/transport verification. Existing GitHub runner returns HTTP 451/202/400 or timeouts; an authorized network/export with chain of custody is the alternative. The conservative hourly mark envelope bounds funding cash but cannot replace the event marks.
- A **genuinely untouched prospective validation and future holdout** are also required after a different complete V98 architecture passes internal training. The already exposed 2025 history and contaminated Phase083 holdout are ineligible for independent final validation.

**Next critical path:** do not rerun or retune OT. Develop a genuinely distinct *complete* seven-slot architecture based on a new preregistered economic mechanism; continue authorized exact-event mark provenance acquisition in parallel. No V98 complete system is approved. No external benchmark or paper/live authorization.
