# V98 Independent Phase261 — Bitcoin NVT DATA_ONLY decision

Status: **FAIL_DATA_NO_ALPHA**.

Phase261 completed its invariant tests and two acquisition attempts, but the exact preregistered Blockchain.com NVT endpoint returned HTTP 404.

Observed evidence from workflow run 38630713046:
- observed days: 0 / 1,096
- coverage: 0%
- source error: HTTP 404
- zero price/return join
- zero direction/threshold selection
- zero parameter search
- zero PnL/backtest
- validation/holdout untouched

The workflow's evidence push collided with a concurrent branch update after the local evidence commit; the run logs preserve the acquisition outcome. This file reconciles that deterministic DATA_ONLY result into branch history. The preregistration prohibited endpoint/provider rescue, so the exact NVT source path is closed.

No Phase261 PnL exists. Phase252 remains the frozen partial architecture.
