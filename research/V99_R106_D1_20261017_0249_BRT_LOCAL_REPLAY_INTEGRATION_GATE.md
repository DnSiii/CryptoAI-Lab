# V99 R106 D1 — 2026-10-17 02:49 BRT pre-economic integration checkpoint

Status: DATA_ONLY / HOLD / NO PROMOTION. No real orders, no historical TRAIN economics, no validation or holdout.

The existing locally packaged D1 modules (research/tools/v99_r106_d1_{basis_carry_preregistered,native_pair_ledger,intrabar_risk,event_clock}.py) and 8 test files were re-executed offline: 85/85 unittest assertions passed. The independent synthetic oracle replayed 2 x 2,000 modeled hours; each case had 498 modeled funding events, 1,999 intrabar risk checks, and 84 daily rebalance calls; maximum accounting identity errors were 1.9984014443252818e-15 (severe) and 4.884981308350689e-15 (supersevere). This proves neither exchange provenance nor trading profitability.

At the start of this cycle, the research branch head was 0c074c6fc8a3cd06791ef7f2366dae9acb1bc705, containing the D1 source-gated preregistration but not the complete D1 implementation or its pre-economic workflow. The latest branch-filtered Actions run was C2 38919570898 from 2026-10-16 14:54 UTC. Thus the offline D1 tests are NOT GitHub CI evidence.

Mandatory next step: integrate the reviewed readable D1 source/tests/workflow on this research branch and run push-triggered CI; then acquire independently authenticated historical OKX spot/perp paired bars, funding schedule and rates, native tier/fill/margin evidence before one preregistered TRAIN economic trial. The current model-only ledger is not a certified OKX settlement or liquidation simulator. Historical R106 holdout diagnostics are contaminated for clean final evaluation.

C1 and C2 remain permanently rejected; immutable V16 Frozen, V99 Frozen, paper history and legacy champion untouched. No paper/result promotion.
