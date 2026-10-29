# V99 R106 I1 — preregistered exact-fold-controlled numeric screening repair (2026-10-29)

## Pre-code hypothesis and defect
The existing provisional/fixture numeric report exposes `numeric_train_pass_both_scenarios` as the conjunction of daily-close fold proxy gates, even when all four immutable TRAIN fold edges are absent or when exact intraday fold recomposition contradicts the daily proxy. Separate `formal_numeric_train_pass_both_scenarios=False` currently prevents promotion, but the ambiguous numeric-pass field can mislead downstream dashboards/decisions and is not a valid five-chronological-fold economic screen.

## Immutable change contract
Without changing candidate, position sizing, source observations, costs, fold timestamps, thresholds or any sealed date: retain the existing daily-proxy gate as an explicitly descriptive `daily_proxy_numeric_screen_pass_both_scenarios`. Define `numeric_train_pass_both_scenarios` strictly as (all four exact fold-edge native NAVs present for both scenarios) AND (severe >=4/5 and supersevere >=3/5 exact positive folds) AND (all other preregistered non-fold numeric gates pass for both scenarios). Exclude only the obsolete daily-proxy `fold_positive` from this final conjunction. Keep `formal_numeric_train_pass_both_scenarios=False` and `exact_chronological_fold_gate_pass=False` until independent original provenance, native fees/funding/margin and fills are authenticated; no promotions, freeze, validation, holdout, orders or paper.

## Independent adversarial test before any data inspection
1. Complete 661 daily synthetic NAV rows with positive daily proxy but no intraday snapshots: descriptive daily pass true; exact-controlled numeric pass false.
2. Four synthetic exact fold snapshots in both scenarios consistent with monotonically positive synthetic daily growth: exact-controlled screen may pass, while formal source certification remains false.
3. Four synthetic exact snapshots with first two fold factors negative, but daily proxy still positive: exact-controlled numeric pass false; independent oracle recomputes and agrees.
4. Missing/duplicate/forged edge or cross-scenario inconsistency still fails closed.

This is a numeric-integrity gate repair, not alpha discovery. All examples are synthetic and cannot establish historical profit. No historical holdout, Frozen, champion, paper/results or orders may be touched. External Deribit 658 missing licensed days and historical native execution costs remain the actual market-data blocker.
