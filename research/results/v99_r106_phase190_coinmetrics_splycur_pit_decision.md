# V99 R106 Phase190 — Coin Metrics SplyCur PIT decision

Decision: **SOURCE REJECTED PRE-PNL / Phase190 not admitted**.

## Evidence

- Coin Metrics documents daily Network Data as computed at 00:00 UTC for the previous 24-hour interval.
- The asset-metrics response schema exposes `{MetricID}-status` and `{MetricID}-status-time` only for metrics requiring human review.
- Critically, `status-time` is documented as the **date of last human review**, not the first machine-publication/availability timestamp.
- Therefore neither the nominal observation `time` nor `status-time` is sufficient to reconstruct, without hindsight, exactly when a historical SplyCur observation first became knowable to a strategy.

## Anti-overfit / causality ruling

A conservative arbitrary lag (for example +24h/+48h) would not establish PIT correctness because historical revisions remain unresolved. Using today's historical SplyCur series would risk revised-data lookahead. No signal, price, return, PnL, fold result, regime result, benchmark result, or holdout observation was inspected for this candidate.

Phase190 is therefore closed before preregistering an economic rule. Reopening requires a source that provides immutable vintages or an explicit first-publication timestamp/revision archive available for the historical TRAIN interval. It may not be rescued by assuming a publication lag after seeing economic results.

## Next research frontier

Continue DATA_ONLY search for orthogonal sources with historical vintages/PIT semantics. Priority: stablecoin issuance/redemption event data with immutable chain timestamps; alternatively on-chain block-native supply deltas derivable causally from finalized blocks. Any candidate must pass provenance, historical coverage, deterministic retrieval, revision/PIT, and holdout-firewall gates before an economic hypothesis is frozen.
