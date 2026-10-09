# V98 Independent — Phase243 cycle 2026-10-09 10:42 BRT

**Decision: DATA_ONLY / NO_CHAMPION / HOLDOUT_UNOPENED.** All writes in this cycle were scoped to `research/v98_independent/` and `.github/workflows/v98-independent-phase243-integrity.yml` on `research/v98-independent-zero`. No V16/V99 source, branch, workflow, report, or paper state was modified.

## Substantive work and evidence

1. **Remote-state and pending-job audit.** Inspected the actual V98 branch, its tree, Phase240 training results, and recent V98-only Actions runs. The prior 2026-10-08 V98 Research workflow was successful but was not a Phase243 integrated historical backtest.
2. **Fixed a cross-engine evidence-contamination risk.** The old Phase243 evidence inventory recursively scanned the entire `reports/` tree and even Python source/tests; any unrelated report with a `phaseNNN` filename could influence V98 eligibility. Replaced it with explicit V98-only report/research allowlists, symlink and path containment checks, explicit status/decision token extraction, and fail-closed treatment of conflicting or absent decisions. Seven synthetic isolation tests passed locally and in CI.
3. **Published source-integrity tools.** Committed an independent seller-residual VWAP conservation validator, its smoke tests, and the fail-closed 185-archive training-only Binance USD-M 1h parser (2022-12 warmup through 2025-12, five frozen symbols). The source parser checks calendar, schema, quote/base units, taker-buy and implied taker-sell conservation, ZIP member identity, hashes and the 2026 holdout firewall. These are source gates, not alpha.
4. **Executed adversarial and reproducibility checks.** The 185-archive synthetic fetch→checksum→canonicalization test completed with 135,240 synthetic asset-hours and identical canonical panel SHA256 `9ceb0394756cf8909d98d472f9eb05bb590e1aea1f15aac83fac18f915078967` in ordinary and optimized Python. Forty focused tests passed locally in each mode. This does not authenticate any historical market ZIP.
5. **Harvester-driven portability correction.** The new remote CI initially failed under pandas 3.0.6 because the code and fixture assumed `DatetimeIndex.asi8` always exposes nanoseconds. Replaced both timestamp conversions with explicit `.as_unit('ns').asi8`. Locally revalidated 40/40 tests in normal and optimized Python; the follow-up remote run was queued/in progress at documentation time.
6. **Independent Phase240 economic re-audit.** Recomputed the 8 specifications × 3 chronological training years × 3 cost cases = 72 recorded outcomes. All 24 base, 24 severe, and 24 supersevere annual results had negative net returns. Best base annual return was -95.7626%, maximum base PF 0.68999; all 72 cost triplets were monotone with rising friction. Phase240 stays REJECT_FAMILY_NO_RESCUE.

## Unchanged research discipline

No Phase243 integrated real-price/funding system PnL has been executed, no rejected family rescued, and no champion promoted. No validation or 2026+ holdout data were opened. The seven-slot architecture remains preregistered but not economically validated. Source downloader publication and acquisition of the 185 official training ZIPs remain outstanding. Binance checksum sidecars alone do not prove the economic value or independently sign authenticity of data.

## Next scientifically justified step

Harvest the final V98-only CI run; obtain original training ZIPs plus checksum sidecars through an approved, reproducible channel; verify all 185 monthly archives and native funding on the same chronological calendar; freeze all seven slot choices before computing integrated training PnL. Report base/severe/supersevere net returns, PF, payoff, win rate, positive days, max drawdown, concentration, tail losses, regime breakdowns, and independent reproducibility. Keep 2026+ holdout unopened until training gates pass.
