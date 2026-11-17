# V98 C9 system-overlay counterfactual protocol — 2026-11-17

Pre-result protocol for the remaining three architecture slots. C9 sleeves and all signal windows remain fixed. Source is the pinned authenticated Clean-4 1h universe, Dec-2022 warmup through Dec-2025, with native funding. No 2026+, XRP, Phase083 holdout, V14/V15/V99 or parameter search.

Counterfactuals at cost scales 1x/2x/4x: (a) full C9 baseline, (b) disable the regime router by replacing its multipliers with 1, (c) disable dynamic allocation caps by using gross_cap=1 and asset_cap=1 instead of 0.75 and 0.40, (d) disable the drawdown governor by replacing its multiplier with 1. All other code, history, funding, execution convention and sleeves remain identical. Record final equity, max drawdown, maximum gross exposure, turnover, and baseline-minus-counterfactual final equity.

These comparisons are **diagnostics**, not an automatic positive-marginal-profit gate. The risk governor may deliberately reduce final wealth to protect against drawdown and tail ruin; the uncapped allocator is explicitly not deployable. Router effectiveness requires chronological stability and sufficient economic materiality, not just one aggregate PnL sign. Do not optimize thresholds, signs, windows, cap values or leverage after observing results.

The existing sleeve ablation passed training only. C9 is not frozen or promoted. The full-run training data already informed C9 assessment, so slicing 2023-2025 post hoc cannot honestly create untouched independent validation. Separate prospective/untouched chronological validation and causality/reproducibility gates remain necessary before freezing, holdout access or external benchmark comparison.
