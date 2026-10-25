# V98 Independent DD — immutable historical rejection (2026-10-25)

**Decision: REJECT_DD_HISTORICAL_GROWTH_OR_MARGINAL.** Do not retune, rescue, or promote DD. The preregistered long-only relative-opportunity mechanism was not economically successful. This is a historical 2023-2024 training-only result, not validated future performance, paper trading, or live authorization.

**Immutable chronology:** preregistration commit `c0477c11ec5e9fd736ced312cce72aaf4921f9c0` before source implementation; seven-slot source commit `aac641747af1ac2eeb92666bdb467628628f1744`; official native historical 20-cell run `40162972759`; independent artifact-only native price/funding/cost audit `40163073560`.

**Authenticated Clean-4 2022-2024 source gate:** PASS; static future perturbation PASS. Effective 2023/2024 epochs: Growth 41/41, Opportunity 5/7, Relative Value 13/14, Stress/Recovery 24/28. No XRP, no 2025 holdout, no 2026+, no external V14/V15/V99 benchmarks.

**Physical execution and independent reconciliation:** 5 paths x base/severe x two native funding orders = 20/20 physically survived, reproduced on Ubuntu 22.04 and 24.04, audit errors []; source SHA consistent. A workflow exit code of success means the *rejection decision was successfully computed*, not that DD passed the economic gates.

**Full 2023-2024 historical training USD10k, carried-before-fill:**

| Metric | Base | Severe |
|---|---:|---:|
| Two-year CAGR | +16.6844% | +3.5239% |
| 2023 net return | +43.7474% | +27.2700% |
| 2024 net return | **-5.2635%** | **-15.7876%** |
| Max drawdown | 32.2495% | 38.3268% |
| Signed native funding | -$1,013.76 | -$862.56 |
| Core-only two-year CAGR | +32.7005% | +20.8031% |
| Full-minus-core final NAV | -$3,998.11 | -$3,879.45 |

**Independent path-level native decomposition (full minus no-sleeve, cumulative USD):**

| Sleeve omitted | Base NAV delta | Base price/interaction delta | Base funding delta | Base extra fees+slip |
|---|---:|---:|---:|---:|
| Relative Value | **-$2,702.73** | -$2,761.18 | +$34.41 | -$24.04 |
| Stress/Recovery | **-$1,886.24** | -$1,953.19 | +$65.34 | -$1.60 |
| Opportunity | **-$1,548.16** | -$1,617.98 | +$22.08 | -$47.74 |

The cumulative identity `NAV delta = price delta + signed funding delta - extra fees/slippage` was independently asserted to 1e-6 USD. It is path-level attribution, **not** an independent event-by-event replay or proof of sleeve standalone alpha. All three satellite marginal gates failed in both funding orders; full-year growth gates failed due to negative 2024 net return and CAGR below thresholds. DD's long-only RV still consumed physical capacity and its negative price/interaction counterfactual overwhelmed favorable funding/cost differences.

**Next critical-path architectural implication (not a retune):** additional long-only sleeves did not solve the core displacement problem. A genuinely different composed engine should test capital-neutral *within-core* relative-weight tilts or another mechanism that does not introduce competing gross inventory; separately test independent event-level attribution and physical core displacement before considering validation. Do not borrow DD rejected source parameters, signs, windows, or budgets.

**Preservation:** Only V98 Independent namespaced files on `research/v98-independent-zero` were written. V16/V99 Frozen, V99 branch/workflows/reports and paper untouched. Sealed 2025 holdout remains unexamined. No real orders.
