# V99 R106 Phase88 — retail-vs-top positioning dislocation TRAIN-ONLY preregistration

Pre-registered only after Phase87 permanent rejection and before any Phase88 return/PnL evaluation.

## Hypothesis
The native Binance USD-M metrics schema contains both `count_long_short_ratio` (broad account positioning) and `sum_toptrader_long_short_ratio` (top-trader position-weighted positioning). Their log-ratio is a structurally distinct positioning-dislocation signal: when broad accounts are more long-biased than top-trader capital, continuation in the opposite direction of the broad-vs-top dislocation is hypothesized.

## Frozen signal
For symbol s and hour t, only when both same-hour ratios are finite and strictly positive:

`raw[s,t] = log(count_long_short_ratio[s,t] / sum_toptrader_long_short_ratio[s,t])`

`signal[s,t] = -raw[s,t-1]`

The minus sign and one-hour causal lag are frozen here. No sign flip after results.

## Frozen execution/evaluation contract
- official Binance USD-M daily metrics archives only; SHA256 + ZIP CRC verification;
- timestamps must be <= registered train_end; holdout files/returns/metrics must not be parsed or evaluated;
- no forward/back fill across missing archives/hours;
- same-hour pairing mandatory; nonfinite/nonpositive ratios are ineligible;
- causal `t-1` signal only;
- gross alpha allocation 0.20, identical portfolio/evaluation machinery and severe-cost assumptions used by Phases82–87;
- chronological train-only selection and the same four temporal folds;
- report train ROI, PF, absolute max DD, positive-hour ratio, robust mean excluding top 1%, valid/healthy folds and concentration diagnostics already required by the gate;
- single hypothesis: no grid, threshold search, alternate horizon, winsorization choice, rescue, sign flip, or post-result retuning.

## Gate
PASS only under the existing train-alpha stability criteria. PASS freezes this exact specification before supersevere-cost, regime-matrix, benchmark-envelope and reproducibility gates. FAIL means permanent rejection and no holdout access.

V16 Frozen and V99 Frozen must not be modified.