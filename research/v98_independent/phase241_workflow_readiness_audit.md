# V98 Independent Phase241 — workflow readiness audit

Date: 2026-10-07. No Phase241 performance was observed.

Independent reconciliation of the frozen preregistration, execution contract, evaluator and validator confirms:
- training cutoff remains strictly before 2026-01-01; annual folds are 2023/2024/2025;
- open(t) decisions consume score(t-1); abnormal-volume rolling median and MAD are shifted one hour; 24h return is consumed only through score(t-1);
- frozen grid is exactly vw {168,336} x k=1 x H {4,8};
- overlapping signals are gross-normalized to <=1;
- PnL uses lagged exposure against open-to-open return; PIT funding is charged against lagged exposure; turnover costs are exactly 7/14/28 bp;
- output includes return, max drawdown, PF, payoff, win rate, positive days, turnover, funding, asset attribution/concentration, daily tails and lagged-BTC regimes;
- validator verifies payload SHA256, finite metrics, exact folds/costs/assets, tail ordering, concentration bounds, and applies the preregistered mechanical gate without rescue.

A Phase241 GitHub Actions workflow was prepared by adapting the already-used Phase240 decision-grade chain (training-only rebuild -> firewall -> two deterministic runs -> byte diff/SHA -> independent validator -> V98-only result commit), but workflow-file creation is blocked by the integration safety layer. This is an execution-path limitation, not a scientific reason to change the frozen experiment.

Status: EXECUTION_READY_NO_PERFORMANCE_OBSERVED. Do not modify the frozen Phase241 hypothesis/grid/gate based on this audit.
