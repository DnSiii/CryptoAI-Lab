# V98 Independent Phase263 — Developer-Acceleration Relative-Value Sleeve

Status: **PREREGISTERED BEFORE COMPLETE PHASE262 DATASET AND BEFORE ANY PHASE263 PNL**.

Execution is authorized only if Phase262 finishes PASS_DATA_ONLY.

## Architecture role

Phase263 is a new **Relative-Value Sleeve** candidate on top of the frozen Phase252 partial engine.

It is distinct from rejected Phase253 price-ratio mean reversion:
- Phase253 used relative prices.
- Phase263 uses exogenous monthly software-development activity.

It also does not increase portfolio net/gross beta: it is a net-zero rotation inside the existing Phase252 exposure.

## Frozen information

Only Phase262 monthly commit counts from the four preregistered repositories may be used.

A trading-month decision may use only **fully completed prior calendar months**. No current-month partial GitHub data.

## Frozen signal

At the 23:00 UTC decision on the **first UTC day of each calendar month M**:

For each asset independently:

1. recent3 = mean commit_count over completed months M-1, M-2, M-3.
2. prior3 = mean commit_count over completed months M-4, M-5, M-6.
3. developer acceleration score = `log((recent3 + 1) / (prior3 + 1))`.
4. If fewer than six completed months are available, no Phase263 overlay is active.
5. Rank the four scores cross-sectionally.
6. Allocate total +0.125 weight to the highest-score set and total -0.125 weight to the lowest-score set.
7. Exact ties at the maximum split the +0.125 equally; exact ties at the minimum split the -0.125 equally.
8. If all four scores are equal, overlay = 0.
9. Hold this overlay until the next first-day 23:00 monthly decision.
10. Add the overlay to frozen Phase252.

Therefore:
- overlay net = 0;
- overlay gross <= 0.25;
- Phase252 net/gross target is preserved because all integrated asset weights remain non-negative;
- no extra leverage is created.

## Frozen constants

- recent activity window = 3 completed months
- prior comparison window = immediately preceding 3 completed months
- score = log((recent3+1)/(prior3+1))
- long overlay budget = +0.125 total
- short/underweight overlay budget = -0.125 total
- rebalance = first UTC day of month at 23:00 close -> next 00:00 open
- all four assets mandatory
- no repo selection, contributor filtering, code-churn substitution, alternative window, threshold, top-N grid, price/funding filter, gross increase, sign flip or post-result rescue

## Frozen comparator

Exact Phase252 partial architecture under identical price/funding/backtester/cost tiers.

## Promotion gate

Phase263 becomes **DEVELOPER_ACCELERATION_RV_CANDIDATE** only if all are true:

1. BASE integrated return > Phase252 by >=3% relative.
2. BASE CAGR > Phase252 CAGR.
3. BASE daily PF >= Phase252 PF.
4. BASE max DD not worse than Phase252 by >3 percentage points.
5. BASE worst day >= -20%.
6. marginal calendar return versus Phase252 positive in at least 2/3 folds.
7. no fold underperforms Phase252 by >5 percentage points.
8. SEVERE integrated return > Phase252 SEVERE.
9. SUPERSEVERE integrated return > Phase252 SUPERSEVERE.
10. at least 18 active monthly decisions exist.
11. no ruin.
12. max open gross <=1.250000001.
13. max absolute overlay net <=1e-12.
14. max overlay gross <=0.250000001.
15. integrated target never becomes negative.
16. max asset contribution share <=70%.
17. top-10 absolute daily-return concentration <=45%.
18. deterministic rerun byte-identical.

Failure => **REJECT_DEVELOPER_ACCELERATION_RV_NO_RESCUE** for this exact 3m-vs-prior3m / ±0.125 overlay. No window, ranking, tie, budget, sign, repo or timing rescue.

Validation/holdout remain locked. V14/V15/V99 remain unused.
