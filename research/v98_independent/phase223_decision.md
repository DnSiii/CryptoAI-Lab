# V98 Independent — Phase223 decision

Status: **REJECT_FAMILY_NO_RESCUE / DIAGNOSTIC_ONLY**

## Evidence harvested

- Corrected decision-grade workflow run `37138243262` completed successfully.
- Training-only canonical data end at `2025-12-31T23:00:00Z`; no 2026+ data entered evaluation.
- Two independent deterministic executions were byte-identical: file SHA256 `bd583ffbd37c2ca8485eca779d2a77af4f4b2ceb57985bf06c437f2d056b2585`.
- Internal deterministic payload SHA256: `aa062ec53018edf6b3ba47256722e59472c6a096c075051bf37b4a2763dff5a1`.
- All frozen-spec/firewall/causality/invariant checks passed.
- Exactly 8 preregistered specs were evaluated on chronological folds 2023/2024/2025 under base/severe/supersevere costs.
- Mechanical gate result: `training-fold coherent specs: []` — 0/8 specs achieved positive base return and PF>1 in all three folds.

## Failure mechanism

The family is not cost-robust or temporally coherent. A representative low-threshold/short-hold spec (`w168_k2.5_h2`) is only marginally positive in 2023 base (+1.04%, PF 1.023) but is already negative in 2024 base (-15.41%, PF 0.960) and 2025 base (-26.96%, PF 0.875). Severe and supersevere costs worsen results monotonically. The same representative spec shows material drawdowns (base MDD about -28.6%, -36.3%, -29.1% across 2023/24/25), weak positive-day fractions, and regime dependence rather than a stable edge. Tail metrics were measured from closed, asset-attributed trades including exit turnover; concentration and funding contributions were retained in the result payload.

## Independence / anti-overfit disposition

Phase223 had already been independently audited as economically overlapping Phase216's idiosyncratic-shock mean-reversion family. Therefore Phase223 was diagnostic/reproducibility-only before result harvest and cannot rescue or promote that family regardless of any isolated cell. The observed 0/8 coherence reinforces the prior family rejection; no parameter narrowing, threshold rescue, regime cherry-pick, or holdout opening is permitted.

## Decision

**Reject Phase223 and keep the broader family closed. Champion unchanged. Holdout remains untouched.**

Next research must be a genuinely orthogonal, preregistered hypothesis selected without Phase223 cell-level optimization and must retain chronological folds, PIT funding, realistic base/severe/supersevere costs, tails/concentration/regime diagnostics, reproducibility, and the 2026+ firewall.
