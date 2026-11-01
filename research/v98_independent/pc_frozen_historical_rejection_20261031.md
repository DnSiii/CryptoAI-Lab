# V98 PC — irrevocable frozen full-system training rejection (2026-10-31)

**Decision: REJECT_PC_TRAINING.** No post-result parameter, sign, threshold, leverage, allocation, or cost rescue. PC is not an approved engine or champion, and simulated returns are not paper/live PnL.

- Pre-result frozen design: `pc_participation_volume_prereg_20261031.md` (commit `d7270751c5419d2a8fe28b7e53e5fecb9f8b87a1`), distinct price-volume impulse / relative-reversal seven-slot architecture.
- Physical 30-cell training: [GitHub Actions run 41266975498](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41266975498), commit `3200ba07b1e2155fbc1c90212f6821de93414721`. This job **failed by design** after reporting economic rejection; all 30/30 physical cells completed and result artifact was uploaded. It was **not** a runtime exception or a passing engine.
- Frozen unmodified `PC_RESULT_JSON` from job logs: `pc_full_training_frozen_result_20261031.json`. Clean-4 source 27,048 hours and 13,524 authenticated native funding **rate** events, Dec-2022 warmup through Dec-2025, with 2025 exposed for exploratory training.
- Independent oracle: 157 weekly decisions and five allocated books, zero signal/allocation mismatches; 26,303 hourly cash identities, zero mismatches; 181 net fill events and funding/fee/slippage independent checks, zero mismatches.
- [Independent frozen-receipt replay 41267114838](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41267114838): **60/60** arithmetic checks, all **24** economic failures reproduced, zero arithmetic discrepancy. This confirms the recorded rejection, not predictive validity.

| Full PC, carried-before-fill | Base | Severe | Supersevere |
|---|---:|---:|---:|
| CAGR simulated | +5.48% | +1.15% | -3.20% |
| Maximum drawdown | -52.31% | -54.50% | -56.60% |
| Turnover USD, initial NAV USD10k | 1,118,503 | 1,050,787 | 984,609 |
| 2025 annual return | -18.52% | -22.21% | -25.78% |

**Why it failed:** base/severe CAGR far below precommitted >80%/>60%; severe drawdown below -45%; negative 2024/2025 annual returns; base/severe turnover >USD1m. Base Opportunity/RV/Stress full-minus-ablation log growth = **+0.00139 / +0.00368 / 0.00000**; severe = **-0.00886 / +0.00366 / 0.00000**; none meets >0.02. Stress sleeve had zero realized marginal contribution. Repeated failures of positive marginal contribution are not solved by changing thresholds after seeing results.

**Source and release blockers are independent of this rejection:** original official 13,524 event `markPrice` objects with raw HTTP/export origin and independent provenance audit remain missing; prior official source attempts returned HTTP 451. A lawfully authorized exchange-origin export with full raw page evidence and hashes is the alternative. Even if those marks arrive, PC remains rejected. No complete V98 has passed internal economics; prospective chronological validation and untouched final holdout remain pending, and external V14/V15/V99 comparison is forbidden until internal freeze and validation. No 2026+, XRP, contaminated Phase083, V16/V99 Frozen, V99 paper, or live trading accessed/modified.

**Next work:** abandon PC without rescue. Prioritize a *genuinely new, preregistered economic source of positive portfolio-wide marginal growth* with capital competition, not another near-duplicate of trend+optional-sleeve recipes; separately pursue exchange-origin event marks through authorized transport. No engine approved.
