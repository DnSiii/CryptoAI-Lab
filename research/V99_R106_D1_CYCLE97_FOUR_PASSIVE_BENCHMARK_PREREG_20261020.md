# V99 R106 D1 — C97 ex ante benchmark amendment (2026-10-20)

**DATA_ONLY/HOLD — NO PROMOTION.** No authenticated D1 TRAIN economic result, no validation or final holdout opened. Original scorer and C1/C2 rejection records are immutable.

C96 established that `carry_no_carry` as a same-fills, zero-funding counterfactual is scenario-specific and cannot be a *common* fourth benchmark across severe and supersevere. This is a fixed-fill accounting attribution, not an investable benchmark. The legacy numerical scorer remains unchanged.

**Preregistered new version C97_PASSIVE_4_V1, before D1 historical economics:** compare against four common fee-free spot-only passive benchmarks with identical initial quote capital and independent reconstruction from strictly causal spot opens: (1) cash, (2) BTC buy-and-hold, (3) initial 50/50 BTC/ETH never rebalanced, and (4) 50/50 BTC/ETH rebalanced at observed UTC-midnight spot opens after valuing prior holdings. The fourth comparator is a frictionless baseline, not realized returns. Benchmark paths must match across both cost scenarios. Preserve all other numerical gates and 5 TRAIN folds; no posthoc changes after historical economics.

Local-only C97 implementation and oracle were tested on a synthetic 120-hour fixture: 13 new adversarial tests, 790 local D1 tests passed total. These are not exchange-certified profits. **Remote source closure and integrated GitHub CI remain pending.** Do not score or promote until the complete versioned code, independent oracle and authenticated native receipts are present and CI is actually run. V16/V99 Frozen, paper/results, legacy champion and final holdout unchanged. No orders.
