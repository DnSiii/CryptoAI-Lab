# V98 Independent Phase251 — pre-result economic-threshold audit

Status: PRE-RESULT / NO PHASE251 PNL INSPECTED.

Phase251's activation rule is not a return-fitted rescue of Phase250.

The router threshold is derived mechanically from execution economics:

- candidate geometry remains the frozen 30/30/20/20 Phase250 target;
- core geometry remains 25/25/25/25;
- BASE trading cost is frozen at 7 bp per unit of L1 turnover;
- for each daily decision, the router calculates the actual L1 cost of moving from the current target to the candidate plus the hypothetical unwind from candidate back to equal weight;
- break-even = that round-trip L1 × 7 bp;
- allocator activates only if the trailing-funding-based estimate of one-day carrying-cost savings exceeds this break-even amount.

The threshold therefore changes only when the required target transition changes. It is not selected from a performance curve and has no tuned multiplier.

Scientific question: can an economically self-funding router preserve Phase250's funding-efficiency benefit without paying opportunity cost continuously?

Failure closes this exact cost-derived router without threshold/lookback/weight rescue.
