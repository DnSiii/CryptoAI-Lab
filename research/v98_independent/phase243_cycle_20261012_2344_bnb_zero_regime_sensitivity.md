# V98 Independent Phase243 — BNB native funding zero-regime and uncertainty audit (2026-10-12 23:44 BRT)

**Scope:** research/v98-independent-zero, V98-native BNBUSDT funding only; 2023-01-01 through 2025-12-31 UTC. No alpha selection, no trade returns, no holdout, no V99/V16 reads or modifications. Data-source identity: Git blob `6b46a2a911d85079f3ce4ec5bc8b1791febd397a`, `research/v98_independent/data/phase206_funding/BNBUSDT_funding.csv`.

## Independent source-only findings

Read the complete V98-native CSV from the specified branch and counted exact Decimal-zero representations, with the 2026-01-01 cutoff exclusive. The 3,288 8-hour training settlements contain **1,800 exact zeros (54.7445%)** and 1,488 nonzeros. Every zero is serialized as literal `0E-8`; six nonzeros have absolute magnitude below 0.000001, demonstrating that zero is not equivalent to a broad near-zero threshold. The V98 archive ingestion code writes the provider's `last_funding_rate` text without numeric quantization, but original monthly archives were not independently re-downloaded in this cycle. Thus this is a canonical-file observation, not independent proof of authentic exchange zeros.

| Year | Settlements | Exact zeros | Zero share | Nonzero abs median (bp) | Nonzero abs p90 (bp) | Longest zero run |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2023 | 1,095 | 507 | 46.30% | 1.4634 | 6.7885 | 66 |
| 2024 | 1,098 | 582 | 53.01% | 2.1015 | 6.1995 | 77 |
| 2025 | 1,095 | 711 | 64.93% | 0.7517 | 2.8026 | 52 |
| Total | 3,288 | 1,800 | 54.74% | 1.4301 | 5.6181 | 77 |

Monthly zero shares vary from **15.56% (2023-11)** to **90.32% (2024-07)**. There are **367** zero runs, including a 77-settlement run beginning 2024-07-03 16:00 UTC. Across all 3,287 adjacent settlement pairs: zero→zero 1,433, zero→nonzero 367, nonzero→zero 367, nonzero→nonzero 1,120. Thus P(zero next | zero now)=79.61%, versus P(zero next | nonzero now)=24.68%. This is descriptive temporal clustering, not a causal or provenance test. Of the 367 fully interior zero runs, 318 have matching signs in the neighboring nonzero observations and 49 opposite signs. That alone does not establish why zeros occur.

## Counterfactual sensitivity, not data repair

The empirical magnitudes of nonzero BNB funding have nearest-rank p50=1.4301 bp, p90=5.6181 bp, p99=12.7869 bp. If *every* recorded zero were counterfactually replaced by the same **absolute** magnitude, the summed gross funding magnitudes on one constant unit of notional would be respectively **2,574.18 bp**, **10,112.58 bp**, and **23,016.42 bp** across three years. These are deliberately extreme diagnostic replacement scenarios, **not** estimates, confidence intervals, plausible worst-case bounds, net funding costs, trading returns, or compound equity outcomes. Direction, position exposure, settlement alignment and whether zeros are genuine are unknown; actual funding remains untouched.

The observed change in zero frequency between years makes a single pooled proxy especially inappropriate. **No zero was imputed or overwritten**, and no performance gate was relaxed.

## Validation and decision

An independent Python Decimal-based training-grid/zero-run/stress auditor and 10 synthetic adversarial tests were prepared locally. Both Python normal and `-O` runs passed (10/10 each); they were **not** run against the complete real CSV locally because this runtime cannot materialize repository bytes from the connector. Real-data descriptive figures above were computed directly from the GitHub connector read and should not be called locally reproduced. Workflow creation and code publication were rejected by safety checks; no workflow was dispatched.

**Decision:** BNB native funding provenance still unauthenticated; XRP 2023-11 monthly 1h physical contradiction still quarantined; Phase240 REJECT; Phase243 BLOCKED_SOURCE; champion NONE. No new backtest and no holdout access. Preserve chronological folds, 7/14/28 bp fees and native funding, regimes, concentration/tails, MDD, PF, payoff, win rate, positive days, reproducibility and anti-overfit gates for any future source-eligible experiment.

**Next source-first step:** obtain publisher-checksummed XRP daily 1h/1m originals for 2023-11-14 and an independently authenticated BNB funding settlement source. Compare timestamps and values before any trading evaluation.
