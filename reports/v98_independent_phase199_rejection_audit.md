# V98 Independent — Phase199 rejection audit

Status: **REJECT_FAMILY_NO_RESCUE**.

Scope is training-only 2023-01-01 through 2025-12-31. Validation and final holdout remain unopened. V16 and V99 were not used.

## Reproducibility / integrity

GitHub Actions run 36806967414 completed successfully after rebuilding canonical data. The temporal firewall passed. Two independent deterministic executions produced the identical report SHA256 `274ade9b20b5a91c3db7a7166ae4fd4f2c1dc141a9370edbb0c74d9a07a9075a`.

Canonical rebuild covered BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT and SOLUSDT through 2025-12-31. BTC/ETH/BNB had zero missing hours; XRP/SOL each had 120 historical missing hours beginning 2022-02-26, outside the scored 2023-2025 folds. This does not rescue or explain the scored failure.

## Scientific result

The preregistered 8-spec funding-pressure mean-reversion family has no winner. Active 24h-lookback variants lose materially: representative `f24_q20_h24` has total return -45.20%, PF 0.929, MDD -64.67%, payoff 1.069, win rate 46.48%, 509/1095 positive days. Severe falls to -69.90% with PF 0.841 and MDD -80.22%; supersevere falls to -88.03% with PF 0.725 and MDD -91.92%.

Fold behavior is unstable and deteriorates chronologically: `f24_q20_h24` returns +15.00% in 2023 (PF 1.103), -20.47% in 2024 (PF 0.935), and -40.25% in 2025 (PF 0.767). The 72h/8h variant shows the same mechanism: +35.48% in 2023, -36.42% in 2024, -43.55% in 2025.

Regime breadth also fails. For `f24_q20_h24`, approximate return contribution is +0.315 in bear, -0.573 in bull, -0.198 in sideways. The bottom-10 negative share is only 11.18%, so the failure is not concentrated in a few catastrophic observations. Concentration is structurally high because with five assets the active dollar-neutral book is effectively one long/one short (`mean_top1_share=0.5`).

## Independent pathology audit

Two preregistered dimensions reveal implementation/data-resolution pathologies rather than hidden edge:

1. `q20` and `q30` are identical for the five-asset universe. With only five names, both quantiles collapse to the same one-long/one-short selection. Treating these as independent confirmations would be pseudo-replication.
2. 72h-lookback + 24h-rebalance variants produce zero scored days / zero turnover and are rejected by the risk invariant. They are not evidence of safety or edge and cannot be promoted.

Neither pathology justifies a rescue. The active variants already fail edge, drawdown, fold consistency, regime breadth, severe and supersevere gates. Reversing the signal, changing quantiles after seeing results, or selecting only 2023 would be post-hoc overfit and is prohibited.

## Decision

**Reject Phase199 as a family, no rescue.** Do not open validation or final holdout. Do not invert or retune this family. Move to a scientifically distinct hypothesis using a different mechanism and preregister it before implementation.
