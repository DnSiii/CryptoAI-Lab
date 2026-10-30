# V98 Independent — Phase240 fee/funding attribution and source continuity (2026-10-09)

**Status: REJECT_FAMILY_NO_RESCUE / DATA_ONLY / NO_CHAMPION.** Training-only 2023–2025. 2026+ holdout unopened; no V99/V16 evidence used.

Frozen source: `research/v98_independent/phase240_results.json`, Git blob `55c13167d1f29683a2a18c3a8e7a695ea090c4f9`, 187921 characters; 8 registered specs × 3 years × 3 cost tiers.

## Independent accounting and economic checks

- Annual compounded returns negative: **72/72**; Profit Factor below 1: **72/72**.
- Negative bull/bear/sideways slices: **216/216**; cases with |p01| not greater than |p99|: **0/72**.
- Maximum simple-sum cost-ladder reconciliation residual: **3.553e-15** (expected base→severe 7 bp and severe→supersevere 14 bp per L1 turnover unit).
- Simple-sum implied zero-fee positives: **9/24**; by year {"2023":0,"2024":4,"2025":5}. Maximum implied break-even charge: **0.503295 bp** per L1 unit, versus frozen base **7 bp**.
- Sum of absolute *net signed* funding contributions across 24 base cells: **0.142372**; sum of nominal base fee charges: **96.215057** in the same reported additive accounting convention; ratio **0.1480%**. Signed net funding may mask opposing per-asset payments; this is a narrow attribution diagnostic, not a stress bound.
- Training source acquisition workflow and source code are now on the V98 branch at `60dd01ef292e54b7bb26f228685a53e70819e447`. This report does **not** claim any historical Phase243 backtest, successful acquisition, or workflow completion.

## Interpretation and gates

The frozen Phase240 failure is broad across cost tiers and regimes, not just a funding-sign artifact. The simple-sum break-even figure must **not** be read as a compounded zero-cost return, quoted fee, or reason to relax the preregistered 7/14/28 bp stresses. Historical Phase240 turnover is a target-turnover diagnostic, not verified Phase243 self-financing fills.

Before any V98 promotion: independently authenticate all 185 Binance USD-M 1h training ZIPs and sidecars; reparse exact 744-hour warmup and 2023/24/25 chronological folds; reconcile five native signed funding files; run self-financing realistic execution, severe/supersevere costs, regime and tail/concentration audits, max drawdown, PF, payoff, win rate, positive days, and deterministic reruns. Preserve 2026+ holdout unopened. No champion promoted from synthetic tests or Phase240.
