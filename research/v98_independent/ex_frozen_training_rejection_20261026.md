# V98 Independent EX — frozen training rejection (2026-10-26)

EX was preregistered **before** economic PnL in commit `8a62903e8439dcf53ec0c983807afc15657d49b2`. No rejected EX parameters, thresholds, signals, weights or gates may be changed or cosmetically rescued. Only Clean-4 2023–2024 training was read; 2025 holdout, 2026+, XRP, Phase083, V14/V15/V99, Frozen and paper remain untouched.

## Physical and source integrity
- Preregistered source-only t-1 future mutation invariant PASS; 2023 active epochs Opportunity 37, Relative Value 42, Stress 9; 2024 Opportunity 31, Relative Value 36, Stress 14. All preregistered minimum-4 activation gates PASS.
- Initial workflow failures were **implementation wiring**, not strategy performance: the cloned economic harness used invalid fee strings `sewere/supersewere`, and the audit incorrectly spelled `new_after_fill`. Both corrected **before valid 30-cell comparison**. Corrected commit `42d27d1a86db427f0c944f593d7fb6247e74dd5a`.
- Valid native execution: **30/30 physical cells PASS**, 22.04/24.04 numeric reproducibility PASS, independent artifact audit errors none. Workflow: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40271738580
- Independent each-hour signed settlement oracle: all five books PASS; **526,290 settled hourly checks and 65,760 funding-event checks**. Same workflow, five oracle jobs.

## Economic decision (2023–2024 training only)
- Full base two-year CAGR **67.334311%**, severe **59.553142%**; severe max drawdown **31.868018%** (carried-before-fill).
- Full base annual net returns: 2023 **97.473964%**, 2024 **41.894717%**. Severe: 2023 **87.981804%**, 2024 **35.510415%**.
- Annual full growth PASS under both native funding orderings for base and severe; full base/severe CAGR and severe drawdown gates PASS.
- **Annual positive marginal contribution FAIL for Opportunity and Relative Value**. Stress/Recovery annual marginal gate PASS. A physically valid high-growth portfolio is **not** a seven-slot accepted engine when two independent sleeves fail locked marginal contribution.
- **FINAL: REJECT_EX_HISTORICAL_GROWTH_OR_MARGINAL.** No 2025 validation, no external benchmark comparison, no paper/live orders. Do not reinterpret physical or accounting checks as economic qualification.
