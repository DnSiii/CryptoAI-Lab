# V99 R106 Phase184 — rejection audit

Decision: PERMANENT TRAIN-ALPHA REJECTION. No retuning. No holdout.

Observed frozen TRAIN result:
- Severe: -40.1851%, max DD -40.5476%, 0/5 positive folds, remove-best-hour -40.5867%.
- Supersevere: -64.4885%, max DD -64.5882%, 0/5 positive folds, remove-best-hour -64.7152%.
- 975 active hours across 18,671 evaluated hours.
- V16 Frozen and V99 Frozen unchanged; post-cutoff market values were not parsed.

Independent mechanism audit:
1. The loss is not explained by one temporal pocket: every chronological fold is negative under both cost assumptions.
2. It is not explained by one lucky/winning tail event: removing the best hour leaves the result deeply negative.
3. Phase183 tested mean reversion and Phase184 tested continuation on the same beta-residual dislocation family; both were decisively negative after costs. Reversing the same residual signal again would be post-hoc sign search, so that family is closed without retuning.
4. Code-level causality review confirms the Phase184 feature window ends with the BTC/ETH return ending at t-1, while PnL is earned from t to t+1. The loader breaks at the cutoff before parsing OHLCV values.
5. Cost monotonicity is economically consistent: supersevere is materially worse than severe. The paired Phase183/184 failure is therefore treated as evidence against this residual-dislocation mechanism, not a reason to weaken costs or gates.

Next scientifically distinct preregistered test: Phase185 BTC-shock → ETH one-hour lead/lag continuation. It changes the mechanism from residual-level dislocation to cross-asset information transmission and keeps the same causal TRAIN-only discipline.
