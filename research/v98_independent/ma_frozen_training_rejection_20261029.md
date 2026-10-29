# V98 MA — immutable source-pass / economic-rejection receipt (2026-10-29)

**TERMINAL REJECTION, NO RETUNING OR HOLDOUT.** New seven-slot MA capital/carry/recovery mechanism was preregistered in commit `c2e2968cb16bdbdd1094ff2fe349f98f3c3f7417` BEFORE source code, source gate, or PnL. All files in this cycle are MA-only under `research/v98_independent/ma_*` or `.github/workflows/v98-independent-ma-*` on `research/v98-independent-zero`.

## Authenticated source-only gate
[Run 40934575791](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40934575791) **PASS**. Original SHA-pinned Clean-4 18,288 hourly bars per asset and 9,144 native signed funding events (2022-12 warmup + 2023-24 training only). Independent event-calendar replay mismatches 0; invalid entries 0; silent updates 0; synthetic and authenticated future mutation prefix PASS; target gross <=0.93. Activation counts 2023: Opportunity **12**, RV **9**, Stress **22**; 2024: **14/10/23**. All pass preregistered >=8/year.

## Physical economic training, NOT independent performance validation
[Run 40934683915](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40934683915) executed all **30** actual hourly physical cells, five books x base/severe/supersevere costs x two signed funding orders. Original Clean-4 and independent SHA-pinned 9,144-event official mark OHLC worst envelope. **CI correctly failed with exit code 2** for economic rejection, and complete JSON artifact **12923118811** was preserved. The receipt was separately inspected; a read-only arithmetic audit independently recomputed all 30 CAGR/log-growth/fee identities, all sleeve marginal differences, funding-order equivalence and physical invariants with zero discrepancy. This is NOT an independent all-hour execution oracle.

| Full book, training 2023-24 | Base | Severe | Supersevere |
| --- | ---: | ---: | ---: |
| CAGR | +70.991% | +67.102% | +63.008% |
| Turnover per USD10k initial | **USD691,736 FAIL** | **USD673,438 FAIL** | USD654,227 |
| Max drawdown | -38.170% | -38.908% | -39.666% |
| 2023 return | +155.292% | +150.237% | +144.770% |
| 2024 return | +14.612% | +11.665% | +8.629% |
| Opportunity marginal net log growth | **+0.019807 FAIL** | **+0.012865 FAIL** | +0.004520 |
| Relative Value marginal net log growth | **-0.016196 FAIL** | **-0.022338 FAIL** | -0.029151 |
| Stress/Recovery marginal net log growth | +0.090542 | +0.080891 | +0.071357 |

Both funding orders produced identical rounded values. **12 preregistered failures** across two orderings: base/severe turnover >USD600k, Opportunity marginal <=+0.02, and RV marginal <=+0.02. These are terminal; do not alter signs, windows, thresholds, weights, fees, or gates to rescue MA. Stress positive contribution cannot be transplanted as a post-result optimization.

## Risk and source limitations
Base/severe one-percent daily CVaR approximately -6.40%; severe daily positive 317/730, severe hourly net profit factor ~1.0394, hourly payoff ~1.0032, hourly win rate ~50.886%, maximum single-asset gross concentration 100% in some hours. Severe signed funding net **-USD2,189.88**, fees **USD673.44**, modeled slippage **USD673.44**, five physical gross trims and no post-trim breaches. These are TRAINING metrics, not independently validated PnL. Exact historical funding-tick mark is still unavailable due HTTP 451; independently checksummed official 1h mark OHLC is a conservative two-sided interval, NOT exact tick. Account-specific fees and actual order-book slippage are assumptions. No independent all-hour PnL oracle, cross-OS, separate 2025 validation, pristine future holdout, external V14/V15/V99 comparison, paper or live trading for MA.

## Economic conclusion and next critical-path hypothesis
MA's RV funding-spread hedge **reduced** compounded wealth and the opportunity sleeve was below the predetermined marginal hurdle despite headline high CAGR. The economic failure is not a source, syntax, or CI failure. A genuinely new complete architecture must derive a positive *joint* relative-value contribution from a different, ex-ante economic mechanism rather than changing MA's parameters or removing its losing short leg. The previous cross-architecture root-cause audit already warns about core financing opportunity cost and repeated 2023-24 selection; additional blind variants are not a substitute for independent chronological validation.

**Decision: REJECT_EARLY_TRAINING_ECONOMIC.** MA permanently frozen; no candidate promoted. Preserve 2025 validation and future holdout, V16/V99 Frozen and paper.
