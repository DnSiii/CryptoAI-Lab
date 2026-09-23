# V99 R106 Phase123 — aggressor run imbalance — decision

Decision: **PERMANENT REJECT** at the severe-cost train gate. Do not repair, sign-flip, threshold-search, retune, or advance this exact hypothesis.

## Evidence
The persisted canonical train report records: ROI `-0.9801267208546834`, profit factor `0.23406519643201598`, max drawdown `-0.9801267208546833`, robust mean ex-top1% `-0.00022589670109235713`, 12 assets, and `stable_train=false`.

All four chronological folds failed the unchanged health criterion:
- F1 ROI `-0.5975309296304413`, PF `0.22794010581109106`, robust mean ex-top1% `-0.0002268307645230298`.
- F2 ROI `-0.6362834128766153`, PF `0.2317037258220195`, robust mean ex-top1% `-0.0002305103539011747`.
- F3 ROI `-0.6539763119164235`, PF `0.23600258627126722`, robust mean ex-top1% `-0.0002269036229311846`.
- F4 ROI `-0.6403832504077477`, PF `0.24075912408861347`, robust mean ex-top1% `-0.0002193195445848929`.

The result is therefore not explained by one temporal fold or by the top 1% of hourly returns. Because the preregistration requires a severe train PASS before downstream stress/regime/benchmark/holdout work, Phase123 stops here scientifically.

## Integrity / causality audit
The report records the fixed pre-PnL 12-symbol universe, train end `2024-01-18T00:00:00+00:00`, causal `t-1` signal shift, no holdout access, missing-data policy `NO_FUTURE_FILL`, and immutable V16/V99 Frozen contract. No evidence from the untouched holdout was used for this decision.

## Family-level implication
Phases121–123 now reject three distinct standalone aggressor-microstructure objects under severe costs: large-trade pressure, aggressive print-count imbalance, and same-side run persistence. This does **not** prove aggressor information is universally useless, but it is sufficient reason not to spend the next hypothesis on another signed-flow variant without genuinely new evidence.

## Next preregistered hypothesis
Phase124 is preregistered independently as unsigned trade-size participation concentration (hourly notional HHI), deliberately leaving buyer/seller direction. Its exact definition and continuation sign were frozen before any Phase124 PnL.