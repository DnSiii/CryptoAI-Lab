# V98 Independent WM — frozen pre-PnL rejection (2026-11-02)

**Decision: REJECT_WM_PRE_PNL_INCIDENCE. DO NOT RETUNE OR REOPEN.** WM preregistration committed at `010ab44dc114ab2becdd1fdd48029ca4acddf50f` **before** strategy implementation and any Clean-4 source run. Original prereg: [WM seven-slot contract](wm_market_neutral_residual_prereg_20261102.md).

## Real executed evidence
[GitHub Actions run 41522559188](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41522559188) on branch `research/v98-independent-zero`, head `4cc55663bf941b1184cea6dbb8096b97e0957e46`, artifact ID **13179255139**, ZIP SHA256 **7280ee01525e775e7f94a5932bda5ebf2e2c0fb248db0544feab36e9ad9c5736**.

The authenticated Clean-4 source loaded through the pinned 2022-2025 bridge, with 27,048 hourly source rows and 13,524 native funding rate events. Synthetic causal future-mutation test passed before the source gate. Across 1,096 UTC daily decisions, measured sleeve incidence was **Growth Core 815; Opportunity 157; Relative Value 507; Stress/Recovery 15**. Preregistered minimum was **30** for every sleeve. Stress/Recovery failed **15 < 30**. This is a testability rejection **before any economic PnL**.

The workflow explicitly emitted `WM_FULL base {"not_run":true}`, same for severe and supersevere; no 30-cell simulation or CAGR is claimed. Separate independent pre-PnL gate auditor confirmed `pnl_computed=false` and no ledger replay, which is correct because no economic ledger exists. The GitHub Actions workflow itself completed successfully, **but the engine was rejected**; workflow success is not strategy approval.

## What this does not prove
No profit, growth, DD, PF, payoff, win rate, positive-day, cost realism, or independent economic performance has been measured for WM. No module can be promoted, and no failed sleeve may be cosmetically adjusted. No benchmarks V14/V15/V99 were read. No 2026+, XRP, Phase083, holdout, V16/V99 Frozen or paper changed. No paper/live authorization.

## Next critical path
Do not revise WM thresholds or rescue the rejected Stress sleeve. Move to a genuinely distinct, precommitted full seven-slot growth architecture, with 30 physical cost/funding-order cells and independent ledger if its pre-PnL gates pass. Exact 13,524 original exchange funding settlement `markPrice` records with authenticated provenance, account-dated fees, historical bid/ask/depth/impact at intended size, and collateral/liquidation rules remain external final-delivery dependencies. The existing checksum-verified hourly mark envelopes are conservative training alternatives, not exact settlement marks.
