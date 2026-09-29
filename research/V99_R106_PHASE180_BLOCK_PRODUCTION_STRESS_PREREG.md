# V99 R106 Phase180 — Bitcoin block-production stress preregistration

Status: DATA/FEATURE preregistration only. No alpha/PnL inspection is permitted until the Phase180 header gate passes on the complete TRAIN interval plus required pre-roll.

## Scientific hypothesis

Bitcoin block production contains an orthogonal network-side stress observable: unusually slow recent block production, relative to the protocol target, may identify mining/network stress not contained in exchange OHLCV. This is a *state variable*, not a directional trading rule.

## Frozen construction (before any PnL)

Source: validated Bitcoin mainnet headers only. Header `time` is miner-declared consensus time and is not treated as exact wall-clock publication time. Every downstream market-bar join must apply an additional t-1 lag after feature construction.

For each validated block h, define `delta_h = time_h - time_{h-1}`. Negative/nonpositive deltas are retained as observed consensus-time pathology and are not clipped into a favorable value.

Only these fixed, protocol-motivated windows are allowed:
- 6 blocks (~1 hour target)
- 36 blocks (~6 hours target)
- 144 blocks (~1 day target)

For each window W, emit only:
- `mean_interval_W / 600 - 1`
- `median_interval_W / 600 - 1`
- fraction of intervals `> 1200s`
- fraction of intervals `> 3600s`

No window/sign/threshold/coin search is allowed. No forward-fill across missing headers. No feature exists until W complete causal intervals are present.

## Causality / selection firewall

- TRAIN selection remains chronological and train-only.
- Holdout begins `2024-01-18T00:00:00Z` and must never be read by Phase180 research.
- Header gate must PASS before feature generation.
- Market alignment applies t-1 *again*; a feature computed from block h cannot affect a bar that could have preceded observation of h.
- Temporal folds, severe/supersevere costs, regime matrix and benchmark envelope remain unchanged if Phase180 ever reaches alpha evaluation.

## Admission sequence

1. Complete header archive + pre-roll passes deterministic consensus/integrity gate.
2. Feature builder passes invariant and reproducibility tests.
3. Produce TRAIN-only coverage/pathology report; reject if coverage is not adequate without imputation.
4. Only then may a separately preregistered directional mapping be evaluated on TRAIN folds.
5. Holdout remains untouched until a candidate is formally frozen under the existing V99 protocol.

V16 Frozen and V99 Frozen are immutable.