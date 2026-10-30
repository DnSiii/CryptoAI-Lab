# IE immutable historical training rejection — 2026-10-27

**Decision: REJECT_IE_HISTORICAL_GROWTH_OR_MARGINAL.** IE is a complete seven-slot *historical training* experiment, not a qualified, validated, benchmarked or tradable V98. No 2025 holdout, 2026+, XRP, contaminated Phase083, external V14/V15/V99, Frozen or paper accessed.

## Source, causality, physical reproducibility
- [Immutable preregistration](https://github.com/DnSiii/CryptoAI-Lab/blob/research/v98-independent-zero/research/v98_independent/ie_native_taker_flow_prereg_20261027.md) preceded implementation and economic PnL.
- [Native Binance OI/taker source acquisition](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40477513000) and [independent artifact integrity audit](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40477926560): 3,011 SHA-verified asset-days, 37 quarantined, 72,264 hourly rows. All 72,264 have taker ratios; one source-zero SOLUSDT 2023 hour explicitly invalidated in any affected 169h window, never filled. Rare >10 ratios bounded in log-space as preregistered before PnL.
- [Official corrected-label IE 30-cell + five-path independent physical oracle](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40479990599): source-only future-mutation causal and missing-data quarantine checks PASS. Financed 2023/2024 epochs: Core 27/26, Opportunity 24/24, Relative Value 24/24, Stress/Recovery 24/24. All **30/30** independently funded USD10k physical scenarios survive, cross-Ubuntu reproducible, zero reconciliation errors; all five independent all-hour ledger oracle jobs PASS (105,258 settled-hour and 13,152 funding-event-hour checks per path). A separate earlier code-identical run 40479944193 independently reproduced the same economics before label-only corrections.
- Official frozen summary artifact `ie30-official-economic-summary` ID 12723340101 in run 40479990599; this note reads only that original summary.

## Frozen IE full training economics (USD10k, carried-before-fill)

| Measure | Base | Severe |
|---|---:|---:|
| Two-year CAGR | +66.6417% | +59.3416% |
| 2023 net return | +80.5860% | +72.6462% |
| 2024 net return | +53.8817% | +47.1561% |
| Max drawdown | 24.3532% | 25.9188% |
| Turnover USD | 413,858.74 | 392,970.19 |
| Native signed funding USD | -1,391.66 | -1,307.35 |
| Fees USD | 206.93 | 785.94 |
| Slippage USD | 206.93 | 1,178.91 |
| Hourly net PF | 1.04686 | 1.04253 |
| Hourly win rate | 51.7159% | 51.6361% |
| Positive UTC days | 390/731 | 387/731 |
| Worst 1% hourly CVaR | -1.5721% | -1.5751% |
| Max single-asset gross concentration | 79.8276% | 79.8276% |

## First-fault full-minus-independent-ablation marginal net log growth

| Sleeve | Base combined | Severe combined | Gate |
|---|---:|---:|---|
| Opportunity | -0.045189 | -0.062248 | FAIL both |
| Relative Value | -0.058254 | -0.072539 | FAIL both |
| Stress/Recovery | -0.004494 | -0.013594 | FAIL both |

All positive-year growth, CAGR, severe drawdown and turnover gates passed; **all three optional sleeve positive marginal gates failed**, including under base costs. This is not a physical-accounting failure or a fee-only issue. IE permanently rejected, no post-result sign/window/threshold/budget/gross rescue or ablation-as-champion. No V98 complete engine approved. Next hypothesis must be economically distinct and preregistered before implementation; only a fully training-approved and frozen system may proceed to separate chronological validation and later external benchmarking. No live orders authorized.
