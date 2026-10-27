# IB immutable 2023–2024 economic rejection — 2026-10-27

**Decision: REJECT_IB_HISTORICAL_GROWTH_OR_MARGINAL.** No V98 complete engine approved. No 2025 validation, no 2026+, no V14/V15/V99 comparison, no paper/live trading.

## Auditable official evidence
- Preregistered before implementation: `ib_preregistration_20261027.md`.
- Source-only gate: [official IB run 40476018579](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40476018579): pinned Clean-4 2022–2024 native USD-M OHLC/quote/funding; future-mutation causality PASS. Active financed epochs 2023/2024: Core 53/52, Opportunity 36/16, Relative Value 26/21, Stress/Recovery 21/19. All pass >=8 preregistered source minimum.
- 5 physically funded USD10k books x 3 cost modes x 2 funding orders x 2 Ubuntu versions = **30/30 physical cells passed**; cross-OS numerical reproducibility and independent artifact-only reconciliation passed. Independent settlement oracle passed all five paths, including IB_full 105,258 settled-hour checks and 13,152 funding-event-hour checks. This proves physical accounting and reproducibility, NOT economic approval.
- [Immutable artifact-only economic first-fault readout](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40476458213) passed, reading only the original 30-cell artifact, no source data or strategy rerun.

## Frozen actual historical training economics, USD10k, carried-before-fill
| Metric | Base | Severe |
|---|---:|---:|
| Two-year CAGR | +57.0813% | +50.8422% |
| 2023 net return | +66.4196% | +58.6089% |
| 2024 net return | +48.3587% | +43.5366% |
| Max drawdown | 23.4157% | 23.9790% |
| Turnover USD | 324,716.91 | 306,951.57 |
| Signed native funding USD | -1,538.34 | -1,447.53 |
| Fees USD | 162.36 | 613.90 |
| Slippage USD | 162.36 | 920.85 |
| Net hourly PF | 1.04238 | 1.03874 |
| Net hourly win rate | 51.8356% | 51.7444% |
| Positive UTC days | 381/731 | 377/731 |
| Worst 1% hourly CVaR | -1.4752% | -1.4742% |

## Exact first economic faults: full minus independently physically re-settled ablation
| Optional module | Base combined net-log marginal | Severe combined net-log marginal | Gate |
|---|---:|---:|---|
| Opportunity | +0.059107 | +0.039575 | PASS in both costs; annual marginals >= -0.03 |
| Relative Value | -0.006923 | -0.058093 | FAIL, both |
| Stress/Recovery | -0.077889 | -0.088787 | FAIL, both |

Core/full positive-year growth, combined CAGR, severe DD and turnover gates passed. **Two optional sleeves failed precommitted positive marginal contribution; full IB is permanently rejected.** A successful Opportunity component inside a rejected full engine is NOT a qualified complete V98, cannot be relabeled a champion or selected as an ex-post ablation. No rescue by sign/window/threshold/budget/gross changes; next hypothesis must be economically distinct and preregistered.

Artifact nomenclature caveat: IB workflow reused legacy artifact prefix `ia30-` despite correct IB payload paths/architecture. Exact run ID, payload architecture `IB`, source digest, path names and independent readout disambiguate; this naming issue is not an economic or settlement discrepancy. Only `research/v98_independent/` and `.github/workflows/v98-independent-ib-*` were modified for IB. V16/V99 Frozen, V99 research/workflows/reports and paper remain untouched.
