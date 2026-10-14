# V98 Independent Phase252 — frozen candidate architecture audit

Status: POST-PASS TRAINING AUDIT / PHASE252 PARAMETERS FROZEN.

Phase252 is frozen as the first reset-era Opportunity Sleeve candidate. This audit does not alter or select any parameter.

## What Phase252 solved

Against the structural Clean-4 core:

- BASE total return: +404.21% -> **+550.57%**
- CAGR: 71.46% -> **86.66%**
- PF: 1.1779 -> **1.2169**
- max DD: -56.39% -> **-52.64%**
- SEVERE: +364.23% -> **+493.66%**
- SUPERSEVERE: +301.68% -> **+408.80%**

Marginal fold contribution:
- 2023: -4.66pp
- 2024: +15.18pp
- 2025: +15.32pp

The sleeve therefore adds large aggregate/stress wealth while respecting the frozen fold-loss tolerance.

## Remaining weakness

The partial engine is not complete:

- 2025 remains negative at **-8.36%** despite being materially better than the core's -23.67%.
- Classified sideways return remains negative (**-37.56%**), while bull and bear classified buckets are strongly positive.
- Max DD remains high at **-52.64%**.
- Phase252 opportunity is active about 25.09% of training hours, so the system still spends most time as structural beta.

## Architecture implication

Remaining modules should not retune Phase252. They should add genuinely orthogonal payoff streams that:
1. improve sideways / weak-trend compounding;
2. preserve the high-growth 2023 regime;
3. improve severe/supersevere terminal wealth rather than merely reduce volatility;
4. avoid broad de-risking that suppresses structural-beta convexity.

Phase253 all-pairs Relative Value is therefore evaluated as a marginal module on top of the exact frozen Phase252 target, not as a replacement strategy.

Validation and holdout remain locked.
