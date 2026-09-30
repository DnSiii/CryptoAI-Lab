# V98 Independent — Phase195 audit

Decision: **REJECT_FAMILY_NO_RESCUE**.

Phase195 was executed twice byte-identically (SHA256 `da82e7c89eb7de6e9dea17c82e44164caf394665d1fd49de0c2061623b98f487`) on training-only 2023-01-01..2025-12-31. Validation and final holdout remained unread; V16/V99 were not used.

## Evidence

All 8 preregistered specs fail the frozen family gate. The least-bad base configuration is the 72h trend / 168h liquidity / 12h hold variant: aggregate return -37.36%, PF 0.956, MDD -64.15%, payoff 1.137, win rate 45.66%. Its folds are +14.53% (2023, PF 1.091), +16.05% (2024, PF 1.100), then -53.00% (2025, PF 0.691), demonstrating decisive chronological instability. Severe return is -68.90% with MDD -77.21% and PF 0.861; supersevere return is -89.78% with MDD -92.40% and PF 0.735.

The family is not rescued by liquidity window or holding period. 24h-trend variants are structurally negative in every fold. 72h variants improve 2023/2024 in some cells but collapse in 2025. Regime sums for the least-bad aggregate are negative in bear and bull and approximately flat/negative sideways. Tail concentration is not a credible isolated failure mechanism: bottom-10 negative share is only ~7.7%, while losses are broad through the path. Position concentration is structurally high (`mean_top1_share=0.5`) because the five-asset universe yields a concentrated long/short construction; no post-hoc diversification rescue is allowed.

The activity diagnostic reports one continuous active episode, so its `insufficient_activity` flag is not interpreted as the causal failure. Rejection is independently compelled by base edge, drawdown, fold inconsistency, regime breadth, and both stress-cost gates.

## Scientific decision

Do not invert, retune, narrow to 2023/2024, change costs, or rescue Phase195. The 2025 reversal is exactly the type of chronological failure the training-fold discipline is intended to expose.

Next research should be scientifically distinct from price-trend plus liquidity ranking. A justified next family is a causal cross-sectional **volatility-shock dispersion / post-shock relative reversion** hypothesis: identify unusually large idiosyncratic realized-volatility expansion using only trailing information, rank contemporaneous residual displacement cross-sectionally, and test whether extreme relative dislocations revert after the volatility shock. It must be preregistered before execution with a small closed grid, the same 2023/2024/2025 folds, funding and base/severe/supersevere costs, regime/tail/concentration diagnostics, and no validation/final-holdout access.