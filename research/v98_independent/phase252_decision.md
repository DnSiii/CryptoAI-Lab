# V98 Independent Phase252 — Opportunity Sleeve decision

Status: **CARRY_SUBSIDIZED_OPPORTUNITY_CANDIDATE / FROZEN FOR ARCHITECTURE**.

Phase252 is the first reset-era V98 module to pass every preregistered training gate.

Frozen partial architecture:
- Growth Core primitive: structural Clean-4 beta, +0.25 BTC/ETH/BNB/SOL.
- Opportunity Sleeve: when the cross-asset mean trailing 168h realized funding sum is <= 0, add +0.0625 per asset; gross rises from 1.00 to 1.25.
- Decision 23:00 UTC close -> next 00:00 open.
- No price signal, no asset rank, no de-risking and no parameter search.

Training evidence, 2023-2025:
- BASE: **+550.57%**, CAGR **86.66%**, PF **1.2169**, max DD **-52.64%**.
- SEVERE: **+493.66%**, PF **1.2078**, max DD **-52.88%**.
- SUPERSEVERE: **+408.80%**, PF **1.1927**, max DD **-53.37%**.
- No ruin.
- Max open gross: 1.25.
- Max absolute asset contribution share: 33.94%.
- Top-10 absolute daily-return concentration: 5.46%.

Chronological folds:
- 2023: **+281.17%**, PF 1.4723, DD -30.98%.
- 2024: **+83.46%**, PF 1.1942, DD -38.36%.
- 2025: **-8.36%**, PF 1.0271, DD -52.64%.

Marginal return versus the structural core:
- 2023: -4.66pp.
- 2024: +15.18pp.
- 2025: +15.32pp.

The frozen gate allowed at most -10pp in any fold and required positive marginal return in at least 2/3 folds. Phase252 passed all gates with zero failures.

## Freeze rule

The exact Phase252 rule is now frozen as an **Opportunity Sleeve candidate**. Its 168h funding window, <=0 activation, +0.0625 per-asset sleeve, 23:00 decision clock and 1.25 system gross cap may not be retuned.

This is not a complete V98 champion and does not open validation or holdout. The next architecture step must add a scientifically distinct module and evaluate its marginal contribution to this frozen partial engine.

V14/V15/V99 remain locked external benchmarks and were not used.
