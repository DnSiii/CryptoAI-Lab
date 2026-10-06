# V99 R106 Phase194A — pre-economic coverage decision

Status: **REJECTED PRE-ECONOMIC / TRAIN_ONLY / economic_trials=0**

This decision closes H194A before any PnL, price outcome, benchmark outcome, regime outcome, or holdout is inspected.

## Frozen evidence used

- Phase192/193 frozen native USDC source only; snapshot SHA256 `de5a6303170e71e0576a4fe7ec66b7094f131bee3ca7b8aaf3dcc95c65799aaa`.
- Phase194 preregistered fixed 24h UTC Mint-minus-Burn transform.
- Phase194A preregistered additive operator (+/-0.05 BTCUSDT and +/-0.05 ETHUSDT).
- Strict eligibility remains `bucket_end < decision_timestamp`; equality is ineligible.
- Holdout and all economic outcomes remained unopened.

## Independent coverage audit

The three frozen source windows yield 15 daily source buckets each before the TRAIN firewall. The third source window extends beyond the frozen TRAIN boundary (18 Jan 2024), so only 8 of its buckets are causally eligible for TRAIN. After the preregistered expanding-history requirement/warm-up, the usable causal decision-source coverage is only about 32 daily observations across three disconnected historical islands.

This is not adequate to support the mandatory H194 TRAIN claims simultaneously:
1. chronological temporal-fold stability;
2. full BULL/BEAR/SIDEWAYS x HIGH/LOW volatility matrix without sparse/empty cells;
3. non-dominance by one fold/regime;
4. severe and supersevere turnover-cost survival;
5. benchmark-envelope and tail/remove-best-period attribution.

Carrying the last observed daily sign through the long unsampled gaps would silently turn sparse source snapshots into synthetic continuous coverage. Extending the source windows after seeing this problem would change the frozen data design. Using 18-20 Jan source buckets would violate the TRAIN firewall. None is permitted.

## Decision

**Reject H194A without spending an economic trial.** The rejection is due to preregistered coverage insufficiency, not poor PnL. `economic_trials` remains **0**.

Do not repair H194A by changing its clock, gross, sign, warm-up, weights, source windows, carry semantics, or operator. A future stablecoin hypothesis must be scientifically distinct and must first obtain genuinely continuous TRAIN-only source coverage under a separately preregistered DATA_ONLY acquisition protocol before any economic hypothesis is frozen.

V16 Frozen and V99 Frozen remain untouched. Holdout remains unopened.
