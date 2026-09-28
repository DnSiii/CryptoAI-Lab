# V99 R106 — Phase175 options-IV feasibility decision + orthogonal borrow-rate candidate

Date: 2026-09-28
Scope: DATA/INTEGRITY ONLY. No PnL, no holdout access, no parameter/sign/threshold search.

## Unit 1 — options implied-volatility source feasibility

The repository audit already established that options-IV would be source-level orthogonal to the exhausted OHLCV / derivatives-positioning / taker-flow / macro families. This cycle searched first-party exchange documentation for a reproducible historical archive spanning the frozen TRAIN period.

Result: NOT ADMITTED. No first-party historical options-IV surface archive with demonstrated point-in-time coverage for the required 2021-12-01 through 2024-01-18 TRAIN interval was proven in this cycle. Therefore no options alpha may be specified or backtested.

## Unit 2 — genuinely new source discovered

First-party OKX historical-data documentation advertises historical **borrow interest rates from December 2021 onward**. This is economically distinct from perpetual funding: it measures spot/margin financing demand rather than perpetual swap carry. The same official archive page separately lists funding history from March 2022 onward, supporting the distinction between the two source objects.

Candidate: cross-asset / quote-asset borrow-rate pressure.

Status: CANDIDATE ONLY — NOT YET ADMITTED.

Why it is promising: source-level orthogonality is materially stronger than another transform of the Phase168 macro panel or the Phase159-164 perpetual-funding family. Borrow demand can represent leveraged spot financing pressure and balance-sheet scarcity.

## Unit 3 — temporal/reproducibility gate before any alpha

Before admission, a deterministic acquisition probe must establish all of the following without looking at PnL:

1. exact first timestamp available for the relevant currencies/instruments;
2. coverage through the full TRAIN endpoint while never requesting holdout observations;
3. stable schema, timestamp semantics and unit definition;
4. missingness/gap map by month and currency;
5. deterministic raw-file hashes / immutable snapshot capability;
6. whether the archive is genuinely market data rather than account-specific data;
7. causal availability rule sufficient to enforce t-1;
8. at least adequate coverage for the predefined temporal folds.

If any of these fail materially, cancel the candidate pre-PnL. Do not repair coverage by shortening TRAIN, changing folds, selecting only favorable currencies, or using holdout data.

## Scientific boundary

No alpha formula, direction, weighting, lookback, threshold, asset subset, leverage or gross allocation is authorized by this document. Those decisions may only be preregistered after the data gate passes. Severe/supersevere costs, regime matrix, benchmark envelope, chronological TRAIN-only selection and untouched holdout remain mandatory for any later alpha phase.

V16 Frozen and V99 Frozen remain untouched.
