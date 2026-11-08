# V98 A2 — authenticated economic replay review (2026-11-08)

Status: **ECONOMIC REPLAY COMPLETE; INDEPENDENT VALIDATION PENDING; NOT PROMOTED**.
Evidence: GitHub Actions run 42506353582, artifact 13626963808. Branch research/v98-independent-zero. Source manifests price 01e7bdeb8bcaf34ee898e322cf20f4479c0e25a9066b40f8cd2446286259f8a8; funding f33094dfc065aa862a529d46f36e15f8a418ab085780214a0423488d2ff49622. Slots c292d67519d189d0c892d5ff1b24438ae0fa7fb728e2c42c3ffd20e518eed602. Execution PREVIOUS_HOUR_DECISION_NEXT_OPEN; holdout_accessed=false. 27,048 hourly steps, initial USD 10,000.

| Cost multiplier | Final equity USD | Full CAGR | Full max DD | Hourly PF | Positive days / 1127 |
|---|---:|---:|---:|---:|---:|
| 1x | 19,142.54 | 23.42% | -22.91% | 1.0447 | 353 |
| 2x | 18,205.50 | 21.43% | -23.44% | 1.0416 | 349 |
| 4x | 16,465.80 | 17.54% | -24.48% | 1.0353 | 343 |

Calendar-year net performance: 2023 +70.38%, 2024 +12.13%, 2025 +0.20% at 1x; 2025 -1.10% at 2x and -3.65% at 4x. Funding 1x cumulative -USD 893.99; execution costs USD 834.00. Hourly PF only modestly above 1 and 2025 nearly flat: regime deterioration is a substantial concern.

**Gate decision:** A2 passes the preregistered minimal *full-sample* checks of positive normal CAGR, positive 2025 normal return, positive 4x *full-period* equity, and completed source/causal replay. This is NOT independent validation. The preregistration explicitly prohibits promotion without chronological folds, independent validation, concentration/tail/payoff and reproducibility checks. Do not interpret full-sample positive CAGR as out-of-sample evidence. A0 and A1 remain rejected; A2 is only a provisional research candidate, not a champion.

**Immediate critical path:** define chronological train/validation partition *without changing A2 parameters*, rerun per-fold economics with native funding, verify per-asset concentration, tails, payoff, reproducibility and positive marginal contributions of all seven slots. Reject if preregistered gates fail. No access to 2026+ holdout or external V14/V15/V99 benchmarks until independent freeze. Do not rescue A2 by retuning on 2025/4x results.
