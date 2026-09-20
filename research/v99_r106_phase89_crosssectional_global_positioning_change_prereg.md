# V99 R106 Phase89 — cross-sectional global-positioning change TRAIN-ONLY preregistration

Pre-registered after Phase87 rejection and Phase88 pre-execution withdrawal, before any Phase89 return/PnL evaluation.

## Motivation / orthogonality
Phase76 tested each symbol's own global account-ratio change as a time-series signal. Phase89 instead tests a cross-sectional relative-positioning mechanism: at each hour, compare simultaneous causal changes across the eligible universe. This is not a sign flip or parameter rescue of Phase76; the information set and portfolio construction are cross-sectional.

## Frozen signal
For each symbol s with positive finite `count_long_short_ratio` at adjacent hours t-1 and t-2:

`chg[s,t-1] = log(ratio[s,t-1] / ratio[s,t-2])`

At decision hour t, rank `chg[:,t-1]` cross-sectionally among eligible symbols. Define centered percentile score:

`score[s,t] = 2 * pct_rank(chg[s,t-1]) - 1`

Direction is frozen **contrarian**: `signal[s,t] = -score[s,t]`.

No threshold: every eligible symbol participates. Ties use deterministic average rank. Fewer than 10 eligible symbols => no Phase89 sleeve exposure that hour.

## Frozen execution/evaluation contract
- official Binance USD-M daily metrics archives only; SHA256 + ZIP CRC;
- train timestamps only through registered train_end; holdout files/returns/metrics must not be parsed;
- no forward/back fill; adjacent-hour changes mandatory;
- causal t-1 information only;
- gross alpha allocation 0.20; normalize absolute signal weights to exactly the available gross budget when eligible;
- identical severe-cost model and evaluation machinery used by the recent train-alpha gates;
- same chronological four temporal folds;
- report ROI, PF, absolute max DD, positive-hour ratio, robust mean excluding top 1%, valid/healthy folds, active hours and concentration diagnostics;
- single hypothesis only: no alternative rank method, quantile cutoff, threshold, horizon, direction, winsorization, universe tuning, rescue or retuning.

## Gate
PASS only under the existing train-alpha stability criteria. PASS freezes the exact specification before supersevere, regime matrix, benchmark envelope and reproducibility gates. FAIL is permanent rejection without holdout access.

V16 Frozen and V99 Frozen must remain untouched.