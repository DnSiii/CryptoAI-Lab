# V98 PO — frozen full-history economic rejection (2026-11-01)

**Binding decision: REJECT_PO_TRAINING permanently.** PO was preregistered at commit `6d80f3c1212cc7838a07aed721e44e4022e0d31e` before implementation and before economic inspection. The physically executed [GitHub Actions run 41323500527](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41323500527) completed all 30 physical cells and an independent audit. Its final workflow failure is the **intentional economic rejection gate**, not a missing source or broken runner. Immutable receipts in this branch: `po_full_training_frozen_result_20261101.json` and `po_frozen_independent_receipt_audit_20261101.json`. No rejected PO parameter, sign, threshold, gross, or funding order can be changed to rescue this hypothesis.

## Exposed-history physical evidence (not holdout)

Four Clean-4 Binance USD-M perpetuals, Dec-2022 warmup through Dec-2025, 157 weekly decisions, 26,303 hourly NAV cash identities; 13,524 native funding events use **conservative hourly mark envelopes, not exact settlement event markPrice**.

| Complete PO portfolio, simulated | Base | Severe | Supersevere |
|---|---:|---:|---:|
| CAGR | **-4.86%** | **-9.07%** | **-13.38%** |
| Max drawdown | -46.40% | -48.33% | -50.41% |
| 2023 return | -32.15% | -35.28% | -38.47% |
| 2024 return | +15.58% | +10.54% | +5.38% |
| 2025 return | +9.81% | +5.08% | +0.23% |
| Turnover, initial USD10k | USD747,351 | USD698,022 | USD649,846 |

Base full: 157 net fill events, one forced safety fill, fees USD298.94, slippage USD149.47, funding **-USD422.29**. 476/1,096 positive days; worst 1% daily mean -5.90%; hourly NAV-change PF 0.9925, payoff 0.9915, win rate 50.03% (**not trade-level statistics**). Peak single-asset gross concentration 100%.

## Independent gates and economic failure

The separately implemented decision oracle reproduced all 157 decisions and all five portfolio books with **zero mismatches**. Hourly accounting independently reconciled 26,303 hours, fees/slippage/funding and net fills with zero mismatches; maximum hourly NAV arithmetic discrepancy 1.82e-12. The separate receipt auditor reproduced **60/60 arithmetic checks**, **20/20 binding economic failures** and rejected **4/4 tamper attempts**.

Base leave-one-out net log-growth marginals: Opportunity +0.00497, Relative Value +0.00331, Stress/Recovery **-0.00450**. Severe: +0.00495, +0.00312, **-0.00439**. All three fail the preregistered >+0.02 marginal gate. PO fails CAGR in both base/severe funding orders; severe also fails max drawdown and positive-all-years gate. Even the core-only book has negative base and severe CAGR. This falsifies the current lagged impulse-propagation seven-slot composition; do not revive it with thresholds or weights selected after observing returns.

## Next genuine delivery steps and external blockers

No complete V98 passed exposed-history gates. Stop treating independently rejected architectures as champions. The next distinct architectural hypothesis must be motivated by an economically independent source of return, not cosmetic variants of trend, rare overlays, OI, premium or PO propagation; source-first basis/term-structure is an option **only** if both legs' authentic history and executable funding/fees are obtained before strategy selection. Avoid more pseudo-phases.

Exact exchange-origin **13,524 funding-event markPrice** values remain absent (HTTP 451). Required: authorized `/fapi/v1/fundingRate` raw response pages (symbol, fundingTime, fundingRate, markPrice), original HTTP Date/headers, request URL, UTC retrieval, raw bytes, SHA256 and independently verified custody; alternative is authorized Binance export with equivalent independent provenance. The V98-only offline ingest now rejects malformed Date, impossible request limit and duplicate raw JSON fields, but a passing structural parser is **not** source-origin attestation. 2025 has already been exposed and cannot serve as pristine validation. Untouched future holdout/prospective evidence, frozen passing system, external superiority comparison and paper/live authorization remain unavailable.

**Scope:** PO preregistration, engine, independent oracle, workflow, full result, independent audit and this frozen decision; separate hardening only to V98-authorized mark ingest. No V16 Frozen, V99, other branches, paper, Phase083, 2026+ or holdout accessed or modified.
