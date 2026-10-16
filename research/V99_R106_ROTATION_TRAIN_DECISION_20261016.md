# V99 R106 — Strict TRAIN-only weekly rotation decision (2026-10-16)

## Scientific decision: PERMANENT REJECT — NO RETUNE, NO PROMOTION

Evidence: official [GitHub Actions run 38901254149](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/38901254149), original artifact `v99-r106-rotation-train-38901254149`, 7/7 adversarial unit tests passed, two evaluator runs produced byte-identical reports. Preregistration committed before seeing economic output at `research/V99_R106_ROTATION_TRAIN_PREREG_20261016.md` under commit `bdcb9f8736a21e831cac63c22c049dfc50827f1e`; only *synthetic fixture tests* were corrected after that commit, not signal/selection code or historical economic parameters.

Fixed strategy: each Monday 00:00 UTC use previous fully completed 720h BTC/ETH returns; long 100% strongest only when BTC and strongest momentum positive, otherwise cash; no shorts, leverage, optimizer, thresholds or parameter search. Historical BTC/ETH canonical hourly *TRAIN* cutoff exclusive 2024-01-18 UTC. Price PnL uses next open and fixed per-side turnover costs; these are **assumed fees/slippage only, before independently verified funding/real order-book fills**, not independently tradable/valid deployable crypto-futures returns.

### Official observed historical preliminary TRAIN economics

| Frozen diagnostic | Severe cost .0007/side | Supersevere cost .0014/side |
|---|---:|---:|
| Whole TRAIN compounded ROI | **+88.2803%** | **+83.5806%** |
| Positive chronological folds | **3/5** | **3/5** |
| Fold 1 | -7.5960% | -8.1145% |
| Fold 2 | +20.6709% | +20.5025% |
| Fold 3 | +7.9452% | +7.1906% |
| Fold 4 | -2.7875% | -3.4683% |
| Fold 5 | +60.9111% | +60.2348% |

Historical static comparators under severe modeled costs over this same TRAIN evaluation: 100% BTC **-25.0632%**, 50/50 BTC/ETH **-34.0567%**. These are narrow TRAIN observations, not forward benchmark validation.

Even with the attractive aggregate result, Phase-specific pre-PnL pass gate required **>=4/5 positive severe folds**, and this strategy achieved **3/5**. Two negative folds and a large final fold contribution undermine consistency. Therefore this exact mapping is **permanently rejected**, not promoted. No rescue by shortening lookback, changing weekly schedule, altering allocation, modifying costs, adding shorts, restricting dates or reweighting assets. A high TRAIN aggregate ROI is not proof of repeatable profit.

**Safety:** `holdout_market_values_parsed=false`, `final_holdout_accessed=false`, `promotion_authorized=false`, `paper_publication_authorized=false`, `real_orders_enabled=false` verified in CI. Frozen V16/V99 and durable paper history were not changed.

## Honest launch-critical assessment

As of this run, no newly tested R106 challenger from today's two one-shot experiments passed all preregistered TRAIN fold-consistency gates: the prior growth breakout had +16.00% severe / +12.93% supersevere but only 2/5 folds; this rotation has +88.28% / +83.58% but only 3/5. Neither is a champion. Do **not** represent the +88% number as verified V99 trading return or combine two rejected models post hoc.

The historical R106 structural research engine `scripts/run_v99_r106_native_all_regime_engine.py` includes explicit full/holdout analysis prior to independent pre-registered freeze; do not re-use its holdout metrics for selecting an alleged clean champion. Build a new clean strict TRAIN -> validation -> final holdout staged engine and require real fee/funding source economics. Keep existing hourly OKX receipts running, but do not fill historical gaps or transfer Binance fee/funding economics to OKX.

**Next engineering priority:** identify a genuinely defensible *complete-engine* economic mechanism with a causal, separate validation contract and end-to-end cost journal; avoid unbounded standalone-parameter/feature testing and avoid deceptive fast launch. Until a complete system passes those gates the valid launch status remains `NO GO`.
