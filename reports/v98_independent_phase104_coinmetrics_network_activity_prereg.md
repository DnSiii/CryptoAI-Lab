# V98 Independent — Phase104 preregistration

Status: FROZEN BEFORE ALPHA/PNL EXECUTION.

Phase103 passed DATA_ONLY for Coin Metrics Community `AdrActCnt` on BTC and ETH with complete 2023-01-01..2025-12-31 daily coverage. Phase104 tests one economically motivated hypothesis only: sustained expansion in active-address activity is a risk-on/network-demand regime for the same native assets; contraction is risk-off.

Frozen rule: at each 00:00 UTC rebalance, use only observations available through the prior UTC day. For each asset independently, compute the sum of active addresses over the latest 7 completed days and compare with the non-overlapping preceding 7 completed days. Long the asset when recent > prior; short when recent < prior; zero on equality/missing history. BTC and ETH each receive absolute gross 0.375, total gross cap 0.75. No thresholds, ranking, scaling, rescue, parameter search, or use of Phase083/V16/V99.

Evaluation is training-only through the configured `training_end`, preserving existing chronological folds. Frozen gates: aggregate return > 0; daily Profit Factor > 1.10; max drawdown >= -35%; every chronological fold return > 0; severe and supersevere each return > 0 and PF > 1.0; single-asset absolute contribution <= 60%; top-10 absolute daily return share <= 60%. Report payoff, win rate, positive days, regimes, concentration/tails and reproducibility hashes. Any gate failure => REJECT_NO_RESCUE. Validation and final holdout remain untouched unless this exact frozen candidate passes training.
