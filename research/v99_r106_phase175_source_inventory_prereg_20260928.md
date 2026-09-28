# V99 R106 — Phase175 source-level orthogonal inventory / preregistration

Date: 2026-09-28
Status: DATA/INTEGRITY ONLY — NO PNL AUTHORIZED

## Why this phase exists

Phase169–174 closed the daily external-macro family after six TRAIN-only failures with the same tail/fold pathology. Earlier frontier evidence also closes cosmetic continuations of positioning/crowding, raw taker/trade structure, return/volatility/residual and simple volume transforms. Therefore Phase175 is deliberately not another alpha formula. It is a source-level orthogonality gate.

## Inventory result

Repository search finds no prior R106 research implementation for either (a) liquidation-event history or (b) options-implied-volatility / Deribit-style volatility surface information. These are source-level additions rather than transforms of the existing OHLCV/funding/OI/crowding/taker/daily-FRED fields.

Candidate A — historical liquidation events:
- economic mechanism: forced deleveraging / mechanical order flow;
- required raw fields: event timestamp, symbol, side, quantity/notional, venue/source provenance;
- minimum causal requirement: point-in-time event timestamps with no reconstructed future aggregation;
- risk: many public exchange endpoints expose only live/recent liquidation streams, not reproducible 2021–2024 history.

Candidate B — historical options volatility surface:
- economic mechanism: forward-looking risk pricing rather than realized-return transforms;
- required raw fields: timestamp, underlying, expiry, strike/delta, option type, mark/IV and source provenance;
- minimum causal requirement: historical snapshots known by t and deterministic mapping to the traded universe;
- risk: historical surface data may require an unavailable external archive and may not cover the full TRAIN interval reproducibly.

## Admission rule

No Phase175 alpha backtest may run until one candidate passes all of the following DATA-only gates on the chronological TRAIN interval:

1. source is reproducible from a documented endpoint/archive;
2. timestamps are point-in-time and auditable;
3. acquisition is bounded to TRAIN before parsing/feature construction;
4. coverage is sufficient across the required TRAIN period and not only recent/live data;
5. deterministic snapshot/hash can be persisted;
6. no holdout rows are downloaded, parsed, inspected or summarized;
7. no PnL, sign choice, threshold, lookback, asset selection or parameter search occurs during feasibility work.

If neither source passes, Phase175 is cancelled pre-PnL. A failure to obtain historical coverage is a data rejection, not permission to substitute a related OHLCV/funding/OI transform.

## Frozen scientific constraints if a source is admitted

Any later alpha specification must be preregistered in a separate commit before PnL and must preserve causal t-1 execution, chronological TRAIN-only selection, temporal folds, severe/supersevere costs, regime matrix, benchmark envelope, reproducibility, and untouched holdout. V16 Frozen and V99 Frozen remain read-only.
