# V99 R106 — post-Phase190 orthogonal source audit

Scope: DATA_ONLY. No price/PnL/holdout observations inspected.

## Candidate A — DefiLlama stablecoin historical series

Public interfaces expose historical stablecoin circulating/minted/unreleased/bridged series by dated observation. This is useful for descriptive research, but the surfaced API/documentation does not provide an immutable vintage identifier, first-publication timestamp per historical observation, or a revision history that would let V99 reconstruct exactly what a live strategy knew at each historical decision time.

**Ruling: reject for predictive backtest input under current evidence.** A current historical endpoint can contain corrected/backfilled history; nominal observation dates alone are not PIT provenance. No economic hypothesis will be run on it.

## Candidate B — immutable chain-native mint/burn events

Scientifically preferable next direction: finalized on-chain Transfer events involving the zero address for stablecoin contracts, because block number/hash/timestamp provide event-time provenance and event history is immutable after finality. This avoids provider-maintained historical supply revisions.

Admission still requires DATA_ONLY proof of: (1) exact contract/version coverage over TRAIN; (2) archive access across the full TRAIN interval; (3) chain coverage decision fixed ex ante; (4) deterministic event decoding; (5) finality lag fixed ex ante; (6) no dependence on current token metadata for historical inclusion; and (7) sufficient coverage without consulting PnL.

USDT/USDC are multi-chain and contract migrations/bridges can make naive Ethereum-only supply deltas incomplete. Therefore no Phase191 economic rule is preregistered yet. First build a provenance/coverage audit; only a passing source can advance to a frozen hypothesis.

## Multiple-testing boundary

The stablecoin family has produced zero economic trials so far. Phase190 was a source-level rejection, not a failed PnL hypothesis. This distinction is preserved to avoid both hidden trials and unnecessary abandonment of genuinely orthogonal information.
