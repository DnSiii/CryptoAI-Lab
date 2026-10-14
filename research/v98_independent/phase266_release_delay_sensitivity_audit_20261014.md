# V98 Phase266 — adverse CFTC publication-delay sensitivity (2026-10-14)

**Scope:** V98 Independent only; 2023–2025 Clean-4, authenticated source SHA-256 checks. This is an independent *price-only* attribution diagnostic, **not** the native funded portfolio backtest, not a candidate promotion or a post-result parameter search. Frozen Phase266 signal, weights, threshold, assets and Phase252 comparator remain unchanged. The stress varies only when the same historical CFTC records are considered usable, by adding conservative delays to the already conservative Phase265 availability ledger.

| Extra release delay | Active hours | ON intervals | Gross price component | Approx 7bp fee-adjusted component |
|---|---:|---:|---:|---:|
| 0 days | 4,896 | 7 | +0.5431% | +0.2981% |
| 1 day | 4,896 | 7 | -1.3691% | -1.6141% |
| 7 days | 4,896 | 7 | -2.8500% | -3.0950% |
| 14 days | 4,896 | 7 | -1.5489% | -1.7939% |

These are **linear overlay-only price contributions** before funding, not compounded portfolio return/CAGR. The original Phase266 diagnostic including its actual funding component and approximate fees was BASE +0.01014%, SEVERE -0.58593%, SUPERSEVERE -1.53353%; those values cannot be reused for delayed variants without recomputing funding settlement timing.

The zero-delay original price component was reproduced to 1e-12 against the prior independent audit. The baseline 2023 gross price component was -1.6544%. Its largest ON cluster accounts for 45.7% of the sum of absolute cluster-level price contributions; top three clusters account for 76.5%. These are cluster attribution shares, **not** portfolio-level day-tail concentration.

**Decision:** Phase266 is NOT promoted. Native exact-simulator BASE/SEVERE/SUPERSEVERE portfolio gates remain unexecuted. No signal adjustment or retrospective rescue is authorized. The CFTC annual archive's historical point-in-time revision risk remains unresolved and blocks final promotion even if a native training gate were to pass. Phase252 remains the partial candidate; complete seven-slot champion: none.

**Evidence:** local reproducible script `phase266_release_delay_robustness.py`, JSON result and nine independent checks; combined with prior price and source controls, **42/42 tests passed** in this cycle. No 2026+, Phase083, XRP or external benchmarks used.
