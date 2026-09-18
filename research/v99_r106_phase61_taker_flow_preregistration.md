# V99 R106 Phase61 — taker-flow hypothesis pre-registration

Status: **PRE-REGISTERED / DATA GATE REQUIRED / NO BACKTEST**.

## Scientific hypothesis
Exchange-native aggressive taker-buy share can exhibit short-horizon order-flow persistence. Before any full-dataset taker-flow distribution or return is inspected, Phase61 fixes one mechanism: **24h cross-sectional taker-flow continuation**.

## Exact feature and direction
For symbol `i` and completed hour `t`, define raw imbalance `I(i,t) = 2 * taker_buy_base_volume(i,t) / volume(i,t) - 1` when volume is positive. Define `F(i,t) = mean(I(i,t-23:t))`, then shift the completed feature by one full bar before any position decision. At decision hour `t+1`, rank `F` cross-sectionally among eligible PIT symbols; continuation direction is long higher `F`, short lower `F` using the same deterministic cross-sectional weighting primitive already used by R106 research. No threshold search, horizon grid, sign flip, or transform alternatives are allowed in Phase61.

## Data gate
Phase61 execution is forbidden unless Phase60 reports `TRAIN_COVERAGE_PASS`. Any missing/checksum/CRC/schema/invariant/boundary failure keeps alpha blocked. No OHLCV proxy is permitted.

## Selection and validation discipline
The 24h transform and continuation sign are frozen by this document before Phase60 results are harvested. Candidate selection uses chronological train only. Features are causal t-1. Temporal folds are mandatory. If train stability fails, reject without sign/horizon tuning. Only a train-stable frozen sleeve may proceed to untouched holdout description/gate, then severe + supersevere costs, regime matrix, concentration/tail diagnostics, and benchmark envelope. Holdout may never choose sign, horizon, threshold, or rescue a failed train result.

## Frozen assets
V16 Frozen and V99 Frozen are read-only and must not be modified. Phase61 is diagnostic research only until all promotion gates pass.
