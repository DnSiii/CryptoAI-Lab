# V98 MN — immutable research decision (2026-10-29 local / 2026-10-30 UTC)

**REJECT_EARLY_TRAINING.** Preregistered BTC-dominance conditional long-BTC/short-negative-alt spread, not a rescue of MM. This decision is permanent. Never retune MN based on results; all other rejected candidates remain rejected. No 2025 validation or 2026+ holdout was opened.

## Evidence
- Prereg: `mn_prereg_20261029.md`, committed before MN source/PnL.
- Source: GitHub Actions run 40994872173 PASS_SOURCE_ONLY; independent 17,544h signals 0 weight/entry mismatches; 27 forced core refreshes; 9,144 native funding events. Entries 2023: Opportunity 9, Relative Value 11, Stress 13; 2024: Opportunity 14, Relative Value 8, Stress 14.
- Full physical run 40994872137: all 30 cells physically survived; 17,543h forensic base/full ledger and independent settlement run within the same workflow. Base/full CAGR 75.791%, severe/full 74.134%, supersevere/full 72.374%; base/full turnover USD276,272 per USD10,000 initial capital. No forward-performance implication.
- Core-only CAGR 73.234% base; base minus-Opportunity 80.028%, base minus-RV 75.892%, base minus-Stress 69.363%. Opportunity and Relative Value *hurt* full net log growth, especially Opportunity 2024. Frozen prereg gates fail: base CAGR <=80%, Opportunity marginal <=0.02 and negative 2024 annual marginal, RV marginal <=0.02. No post-result sign/window/threshold/gross rescue.
- Read-only independent audit run 40994968988: 30/30 arithmetic cells reconciled (0 arithmetic mismatches), 17,543h original strategy-to-fill replay (0 quantity mismatches, synthetic tamper detected), 17,543h independent signed native funding settlement and hourly PnL reconciliation. The run was marked failed only because an accidentally duplicated *extra* fill-oracle command referenced nonexistent /tmp/mn_native; the three substantive audits had already passed. The redundant command was removed without modifying engine/source/receipts. Replacement read-only audit run 40995034432 pending at this writing.

## Integrity
Only branch `research/v98-independent-zero`, V98 namespaced files. XRP remains quarantined; no V16/V99 Frozen or paper state touched. Mark envelope is conservative and SHA-pinned but not independently attested exact event mark price; exact funding mark provenance remains open. No engine promoted, no paper/live permission. Next step: genuinely different seven-slot economic hypothesis, with unchanged prereg/chronological/holdout discipline; do not recycle MN.
