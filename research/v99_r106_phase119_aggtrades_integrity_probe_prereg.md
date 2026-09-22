# V99 R106 Phase119 — raw aggTrades deterministic integrity/throughput probe preregistration

Phase119 is an **INGESTION INTEGRITY / RESOURCE FEASIBILITY PROBE ONLY**. It follows Phase118 availability evidence and runs independently of all alpha candidates.

## Why this probe exists
Phase118 found perfect daily object coverage across all four existing folds for all 48 canonical symbols, but the full pre-train archive is about 95.36 GB compressed. Before spending a full-run budget, verify the raw file schema/integrity and measure a deterministic sample's ingestion burden without evaluating any trading hypothesis.

## Frozen sample
For every canonical PIT48 symbol, download exactly the first calendar date of each existing daily fold:
- F1: 2021-12-01
- F2: 2022-06-14
- F3: 2022-12-25
- F4: 2023-07-08

Total target: 192 official daily aggTrades archives, all already shown as available by Phase118.

## Checks
- Official Binance USD-M `daily/aggTrades` only, plus matching CHECKSUM.
- SHA256 and ZIP CRC.
- Exactly one nonempty CSV member.
- Accept headered or headerless official schema; data rows must contain the seven documented aggregate-trade fields.
- Parse integer aggregate/first/last trade IDs and timestamps; require first_trade_id <= last_trade_id.
- Price and quantity must be finite and strictly positive.
- Buyer-maker value must be a valid boolean representation.
- Within each sampled file, aggregate-trade IDs and timestamps must be nondecreasing; duplicate aggregate-trade IDs are prohibited.
- Record row counts, compressed bytes and wall-clock ingestion time only for resource planning. Do not report price/quantity distributions.

## Prohibited
No return/PnL relation, no resampling into alpha features, no buyer-maker imbalance, no direction, horizon or threshold, no regimes/benchmarks, no holdout archive content.

## Decision
A clean Phase119 can justify designing a separately preregistered raw-microstructure feature only if resource feasibility is acceptable. It does not authorize an alpha by itself and cannot weaken any R106 gate.

V16 Frozen and V99 Frozen remain immutable.
