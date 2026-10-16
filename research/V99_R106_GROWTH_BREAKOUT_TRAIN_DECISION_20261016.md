# V99 R106 — 2026-10-16 economic TRAIN gate decision

## Decision: REJECT (NO RETUNE / NO PROMOTION)
This note memorializes exactly ONE independent fixed hypothesis and its first official research CI evidence. It does not open the final holdout, alter a published paper, or claim real-exchange performance.

GitHub Actions successful run: [38898868129](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/38898868129). The run restored the existing canonical market cache; seven synthetic/causal tests passed, and twice executing the fixed evaluator yielded identical report bytes. Original output is retained under `v99-r106-growth-challenger-train-38898868129`, not published into a champion ledger.

The preregistration was committed BEFORE first economic PnL to `research/V99_R106_GROWTH_BREAKOUT_TRAIN_PREREG_20261016.md`. The test used BTCUSDT and ETHUSDT hourly canonical source, decision rule fixed at 168h Donchian breakouts/72h midrange exits, 00:00 UTC daily changes, 168h lagged-vol allocation, max total gross 1.25, exclusive TRAIN cutoff 2024-01-18T00:00Z. No parameter search or post-result inversion.

Measured **TRAIN-only, preliminary before authentic settled funding**:
- Severe assumed fees/slippage 0.0007 per side: **+16.0021961470%** compounded gross-minus-assumed-cost; only **2/5** five chronological folds positive: [+7.0798%, -4.8423%, +19.8085%, -1.0363%, -3.9824%].
- Supersevere assumed fees/slippage 0.0014 per side: **+12.9314493651%**; only **2/5** chronological folds positive: [+6.2167%, -5.4854%, +19.3891%, -1.3674%, -4.4704%].
- Gating policy required >=4/5 positive severe folds and >=3/5 positive supersevere folds, among other preregistered gates. Therefore it **FAILS irreparably** regardless of positive aggregate historical ROI.
- `holdout_market_values_parsed=false`, `final_holdout_accessed=false`, `realized_funding_authenticated=false`, `promotion_authorized=false`, `paper_publication_authorized=false`, `real_orders_enabled=false`.

## Development prioritization
The shortest truthful path is NOT another chain of near-duplicate audits or retrospective rescue of this strategy. Keep first-party OKX receipt collection and paired-chain auditing on existing background GitHub Actions, but separately undertake ONLY genuinely distinct preregistered TRAIN-only economic hypotheses or integrate already eligible frozen TRAIN components. Do not select on previous paper losses or inspect existing R106 full-history/holdout diagnostics for tuning.

**Important existing technical debt:** `scripts/run_v99_r106_native_all_regime_engine.py` historically computes an explicit `holdout` analysis and full-sample/supervised comparisons inside `main()`, prior to any new formal freeze. Treat historical R106 holdout diagnostics as contaminated for candidate selection and do not recycle them as an untouched final holdout. A new isolated strict TRAIN + separate validation pipeline is necessary; final holdout remains closed. Do not weaken integrity thresholds merely to deliver earlier.

A PRE-FUNDING train-return result is neither authenticated net futures PnL nor a profitable deployable engine. Retain existing R106 F7/F9 historical research reference under its documented quarantine; do not modify V16 Frozen, V99 Frozen, any old five-track ledger, or the protected final holdout.
