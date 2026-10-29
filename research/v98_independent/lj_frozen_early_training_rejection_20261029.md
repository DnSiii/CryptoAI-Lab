# V98 Independent LJ — permanent early training rejection (2026-10-29)

**FINAL LJ DECISION: REJECT. NO RESCUE, NO PROMOTION, NO HOLDOUT.** This is a source-validated candidate that failed an early *local* economic diagnostic. No original 30-cell GitHub Actions workflow, no independent all-hour ledger oracle, no independent 81-corner physical settlement, no cross-OS replay, no 2025 validation and no external benchmark comparison were performed for LJ. No real trading.

## Chronological provenance
- Seven-slot preregistration was committed **before** implementation and before any LJ source counts or PnL: `1f7229c7bf80cbd6ae0a3c83746f47a5a19377d6`.
- New self-contained SHA256-attested source reader: `v98_clean4_training_reader.py`. Frozen source `lj_sources.py`, independent source replay `lj_independent_source_gate.py`, local signed-collateral diagnostic `lj_local_physical_diagnostic.py`, all within `research/v98_independent/`.
- Authenticated original pinned training artifact: GitHub Actions artifact ID **12549265452**, 18,288 hourly OHLC rows per BTC/ETH/BNB/SOL, December 2022 warmup through December 2024; exact four vendor OHLC SHA256 matched official receipt. Native signed funding/mark bounds **9,144** rows and SHA256 `f706812b7989666c3efd0b24045a5c31f4d9c79b46d61da7b5e6cde6c6e73f5e` verified. One simultaneous zero-quote hour at row 16748 handled causally.
- **Independent source-only event replay passed**: zero entry mismatches, 2023 Opportunity/RV/Stress **24/15/14**, 2024 **26/10/15**; all >=8. Synthetic and authenticated 14,000h future mutation prefix passed; no silent source row updates, no invalid quote entries, intended max gross **0.88**. The receipt is `lj_authenticated_source_receipt_20261029.json`.

## Rejection-only local signed-collateral diagnostic
Executed ten training-only physical cases: five fixed books (core/full/three single-sleeve ablations), base and severe costs, carried-before-fill funding order. USD10k initial. Actual t+1 open execution, native signed funding, independent signed row inventory, non-netted gross, fee+slippage, no hidden leverage, local adverse intrabar low/high equity check. **This local engine is not the official original settlement oracle.** Local PF/payoff/win rate are intentionally NOT claimed: no independently reconciled realized trade ledger.

| Local metric | Base | Severe |
|---|---:|---:|
| Full two-year CAGR | **+39.075%** | **+33.610%** |
| Core-only two-year CAGR (ablation, not promotable) | +36.356% | +32.964% |
| Full 2023 return | +58.965% | +52.836% |
| Full 2024 return | +21.674% | +16.803% |
| Full max drawdown | -33.111% | -33.907% |
| Full turnover per USD10k | **USD827,743** | **USD791,876** |
| Full native funding cash | -USD1,016.13 | -USD967.80 |
| Full fee cash | USD331.10 | USD791.88 |
| Full slippage cash | USD165.55 | USD791.88 |

Local full-minus-ablation **two-year net log growth** (precommitted requirement >+0.02 in BOTH tiers):
- Opportunity: base **+0.02024**, severe **+0.00349** — severe FAIL.
- Relative Value: base **+0.02876**, severe **+0.02060** — local marginal passes narrow numeric floor, but not independently validated.
- Stress/Recovery: base **-0.01024**, severe **-0.01511** — FAIL.

## Locked gate failures and decision
1. Base CAGR **39.075% < 50%** hard threshold: FAIL.
2. Base and severe turnover **USD827,743 / USD791,876 > USD600,000**: FAIL.
3. Opportunity severe marginal **+0.00349 < +0.02**: FAIL.
4. Stress/Recovery base and severe marginals **negative**: FAIL.

All four are terminal **pre-registered** economic failures. LJ is permanently rejected; do not change signs, thresholds, clocks, windows, gross, source policy, or costs to rescue LJ. No need to spend 30 original cells, 60 independent receipts or untouched validation on a failed candidate.

## Physical boundary diagnostic and reproducibility blocker
- The same frozen full book, replayed locally at the alternate `new_after_fill` native funding order, produced **USD0.00 difference in final NAV** for both base and severe, because LJ events did not cross native funding boundary with changing inventory in the observed sample. This is *not* independent oracle certification.
- A repository tree audit found **`ko_source.py` and `ko_physical.py` absent**, despite `li_local_diagnostic.py` importing them. LI's claimed local economic diagnostic therefore cannot be reproduced from the checked-in branch without missing dependencies. This is a concrete reproducibility defect, not evidence that LI should be rescued.
- Connected GitHub API provides repository reads/writes and Actions status, but **no workflow-dispatch POST**; existing candidate workflows trigger only on their own explicitly listed files. LJ is not eligible for original CI because it already failed hard economic gates. For any future passing candidate, the authorized alternatives are (a) an external GitHub Actions dispatch capability, or (b) an authorized equivalent runner with independently reconciled full 30-cell outputs; a local diagnostic alone is never promotion.

## Next architectural work
Pursue a **genuinely distinct** complete seven-slot economic mechanism with lower turnover and robust positive marginal contribution of all optional sleeves to the *complete shared-collateral book*. Focus on fewer rebalance events and episodic opportunities that survive severe costs, not incremental edits to LJ. Keep Phase243 Clean-4 source firewall, native funding, untouched 2025+ and Phase083, V16/V99 Frozen and paper. No candidate currently approved and no real orders.
