# V98 Independent Phase220 — decision-grade postmortem

Status: **REJECT_FAMILY_NO_RESCUE**.

## Evidence harvested

The corrected exact-MAD run completed successfully after the pre-result implementation defect had been quarantined. The decision-grade payload identifies `mad_definition=exact_same_window_median_absolute_deviation`; deterministic reruns were byte-identical with SHA256 `ba14f2f198eba173cf3feb2f5464d333e1a2b38d9f03e5edc3b804d3b098ce5b`. Workflow invariants confirmed the `<2026-01-01` firewall, chronological source ordering, no duplicate timestamps, the frozen 8-spec grid, causal `t-1` construction, exact same-window MAD, gross exposure <= 1, and monotonic base/severe/supersevere stress returns.

Mechanical gate result: **0/8 training-fold coherent specs**. No spec had both positive base return and Profit Factor > 1 in all of 2023, 2024 and 2025. Therefore the family is rejected without parameter rescue, sign inversion, regime rescue, asset cherry-picking, or holdout access.

## Failure mechanism audit

Representative frozen spec `funddisp_N21_S10_hold4` already fails before stress: 2023 base return -10.30%, PF 0.9924, MDD -35.27%; 2024 base return -7.72%, PF 0.9973, MDD -46.92%. Costs worsen the same mechanism materially (2023 severe -19.82%, supersevere -35.94%).

The cross-sectional legs are unstable across assets rather than expressing a broad relative-value edge. In 2023 BNB and SOL are positive while ETH and XRP are negative; in 2024 BNB is strongly positive while SOL/XRP are negative. Max asset concentration is already ~41-48% in the representative base folds, so aggregate near-breakeven PF is not evidence of diversified robustness.

Regime attribution also rejects a rescue interpretation. For the representative spec, 2023 bull is -16.77% / PF 0.9486 while bear and sideways are only modestly positive; in 2024 bear is +12.51% / PF 1.0627 but bull and sideways are negative. This is regime rotation, not a stable causal premium. Severe/supersevere costs erase marginal pockets further.

Tail diagnostics are not used for selection. The representative 2023 base worst trade is -4.52% versus best +6.49%, while 2024 worst trade reaches -7.28%. These observations support the rejection but do not motivate any post-hoc threshold change.

## Scientific decision

Phase220 is closed as a failed family. The invalid pre-correction run remains non-decision evidence; only the exact-MAD rerun above is admissible. The 2026+ holdout remains unopened. Champion state is unchanged. No V16/V99 branch, workflow, report, or paper state is touched.
