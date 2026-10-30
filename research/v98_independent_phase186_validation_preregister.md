# V98 Independent — Phase186 untouched validation preregistration

Status: **PREREGISTERED / CONFIRMATORY VALIDATION / FINAL HOLDOUT CLOSED**

## Candidate frozen before validation PnL

Validate exactly the Phase185 frozen WALCL candidate, with no modification:

- native weekly FRED `WALCL`;
- `WALCL_4W_CHANGE = WALCL_t / WALCL_{t-4} - 1`;
- conservative next-UTC-day availability and forward carry only;
- change < 0 => gross multiplier 0.50; otherwise 1.00;
- identical underlying V98 stack, costs/funding, severe/supersevere schedules and gross-cap;
- no threshold/lookback/sign/multiplier/asset-specific search and no rescue.

## Window firewall

Use only the already-established V98 untouched validation window **2026-01-01 through 2026-07-31**. Final holdout beginning **2026-08-01** remains closed and must not be downloaded, inspected, summarized, or used. Training results may be referenced only to verify the frozen identity, never to retune.

V16/V99 files, workflows, reports, paper state, metrics and candidates may not be read or used.

## Required validation report

Report base/severe/supersevere total return, max drawdown, Profit Factor, payoff, win rate, positive days, chronological monthly breakdown, market regimes, concentration by asset, tails, asset contribution, gross-cap and deterministic rerun identity. Explicitly report WALCL causal availability and assert that no timestamp >=2026-08-01 entered prices, funding, macro data or evaluation.

## Confirmatory decision gates

Apply the existing V98 validation gates unchanged, including PF > 1.02, max drawdown >= -35%, positive severe and supersevere returns, no ruin, gross-cap compliance, deterministic rerun identity and all existing integrity/causality invariants. Any mandatory failure => `REJECT_VALIDATION_NO_RESCUE`. Only a complete untouched validation pass may be frozen for a separately preregistered final-holdout phase. No final holdout may be opened here.