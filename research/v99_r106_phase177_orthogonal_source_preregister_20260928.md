# V99 R106 — Phase177 orthogonal source preregistration

Date: 2026-09-28
Status: PREREGISTERED DATA-DISCOVERY ONLY

## Motivation

Phase169-174 exhausted the recent macro family without temporal robustness. Phase175/176 then investigated genuinely orthogonal external data. The OKX borrowing-rate archive remains blocked on point-in-time provenance, so no alpha/PnL may be formed from it.

Phase177 therefore searches for a scientifically distinct first-party dataset rather than rescue-tuning Phase176.

## Candidate family

**Crypto options implied-volatility / term-structure history from a first-party exchange or venue.**

Economic mechanism, specified before any return inspection: option-implied volatility and its term structure encode forward-looking demand for convexity and crash insurance that is not equivalent to realized OHLCV volatility, perpetual funding, open interest, taker flow, crowding, premium-index dislocation, order-book depth, or the rejected macro panel.

## DATA gate before any alpha

A candidate source is admissible only if all conditions pass:

1. first-party venue/source;
2. immutable or demonstrably point-in-time observations;
3. coverage sufficient for the frozen TRAIN and temporal folds, with no shortening of TRAIN to fit the source;
4. explicit observation/publication timestamps and UTC semantics;
5. documented units and instrument identifiers/expiry/strike semantics;
6. deterministic acquisition and SHA-256 manifest;
7. no post-TRAIN rows inspected for feature choice or parameter selection;
8. causal availability permits an additional t-1 lag;
9. no PnL, sign search, threshold search, expiry search, strike search, asset search, or window search during DATA gate.

## Precommitted failure rule

If no first-party options-IV source can prove full frozen-TRAIN coverage plus point-in-time semantics, reject Phase177 as a data candidate. Do not replace missing history with vendor backfills of unknown provenance and do not relax the TRAIN boundary.

## If DATA gate passes

Only then write a separate alpha preregistration before inspecting returns. Severe/supersevere costs, temporal folds, regime matrix, benchmark envelope, tail/concentration audit, reproducibility, chronological train-only selection, and untouched holdout remain mandatory.

V16 Frozen and V99 Frozen remain untouched.
