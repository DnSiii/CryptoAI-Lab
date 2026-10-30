# V98 Independent Phase212 — post-mortem

Status: **REJECT_FAMILY_NO_RESCUE**

Phase212 tested the preregistered range-position exhaustion reversal family on chronological training folds 2023/2024/2025. The workflow rebuilt training-only data, passed the `<2026-01-01` firewall, executed the evaluator twice, and produced byte-identical result files (`sha256 7cfaebb2b0dd73a82a8550e68029e61c52f5f1c1998639c2f8797bbba150348d`). The mechanical training gate found zero coherent specs out of eight.

## Independent failure audit

The first frozen spec (`range_L168_z25_hold3`) is already decisively uneconomic in 2023 under base costs: return -19.37%, PF 0.876, MDD -22.14%, positive days 29.0%. Severe costs worsen return to -36.14% / PF 0.762 / MDD -36.33%; supersevere to -59.96% / PF 0.593 / MDD -60.00%.

The 2023 loss is not a single-asset accident: BNB -10.34%, ETH -3.59%, SOL -3.57%, XRP -3.05%. Nor is it rescued by broad regime conditioning: bull -6.51% (PF 0.911) and sideways -15.09% (PF 0.747); only bear is slightly positive at +1.57% (PF 1.053), which is insufficient and cannot justify a post-hoc regime filter.

Tail economics are also unfavorable: base p01 -1.413% versus p99 +1.139%, worst trade -2.554% versus best +1.623%. Payoff above one does not compensate for the very low trade win rate (~7.55%) and weak positive-day fraction. Transaction-cost sensitivity is severe, confirming inadequate gross edge rather than a marginal implementation issue.

Conclusion: do not invert, retune thresholds, isolate the one favorable regime, select assets ex post, or otherwise rescue Phase212. No validation/final holdout was opened and no champion change is warranted.

## Next scientific direction

The next family must be orthogonal to recent funding-dislocation, residual-momentum/dispersion, hour-of-week residual, BTC lead-lag, and range-exhaustion families. Prefer a causal feature that captures a different market mechanism and can be computed strictly from training-only OHLC/funding data without using V99 evidence. Freeze the hypothesis/grid before evaluation and retain identical chronological folds, realistic funding, base/severe/supersevere costs, concentration/tails/regimes and reproducibility gates.
