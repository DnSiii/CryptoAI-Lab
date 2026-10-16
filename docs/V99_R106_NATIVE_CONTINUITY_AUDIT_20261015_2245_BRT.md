# V99 R106 — 2026-10-15 22:45 BRT research evidence / DATA_ONLY

Scope: `research/v99-r106-native-all-regime-engine`. Frozen V16/V99, untouched holdout, and champion history are excluded from edits.

## Official observations, checked 2026-10-16 01:45 UTC

- Durable immutable receipts branch: `research/v99-r106-live-receipts`, observed head `b200e5afcfb8fb6133d498b71640a10458379f3c`.
- Market buckets: 2026-10-14T20,T23; 2026-10-15T01,T07,T13,T18,T20,T22,T23; 2026-10-16T01.
- Native terms buckets: 2026-10-14T20,T23; 2026-10-15T01,T07,T13,T17,T20,T21,T23; 2026-10-16T00.
- Intersection: 7 paired buckets (14T20,14T23,15T01,15T07,15T13,15T20,15T23) out of 30 hourly UTC buckets from 14T20 to 16T01 inclusive. **23 missing paired hours; longest consecutive paired run is 1.** Market-only and terms-only hours must never be retroactively paired or backfilled.
- First-party source-only Actions 38836170283 and 38836061785 succeeded around 01:37–01:38 UTC, but neither is evidence of an immutable atomic paired hour or economic trading result.
- Official V99 Frozen paper-results snapshot at 2026-10-16 00:00 UTC: 938 simulated forward hours, equity multiple 0.850575 (ROI -14.9425%). This is **V99 Frozen paper**, not R106 PnL.
- The separate five-variant R98/R106 comparison snapshot still ends 2026-10-10 05:00 UTC. Its tracking figures are stale and **not eligible for promotion**.
- Original 2026-10-15T23 → 2026-10-16T00 public OKX terms artifacts (from prior research cycle) were independently replayed: 5 event IDs matched; 4 forecast rates differ from subsequently published settled rates. Published rates are not position-specific funding cashflows, and no fee tier or order journal was authenticated.

## Causal/economic gates

- t-1: accept only confirmed candles whose close preceded the recorded first-party receipt; conservative earliest decision remains separately enforced.
- Funding: require an actual *pre-event* forecast capture and an actual *post-event* settled-rate publication. Matching event IDs and SHA-256 hashes do **not** authenticate realized position cashflows.
- Preserve chronological train-only selection, temporal folds, untouched holdout, regime matrix, severe/supersevere costs, benchmark envelope, reproducibility, and anti-overfit gates.
- DATA_ONLY/HOLD remains mandatory. Do not transfer Binance R106 fee/funding assumptions to OKX. No new champion, paper ROI, or promotion is claimed.

## Next preregistered, non-overfitting step

1. Integrate and CI-test fail-closed funding event capture bracketing and verified market predecessor selection (read-only, no strategy/holdout).
2. Fix the stale first-page Actions artifact selector only after checking both Actions and durable source precedence, then test adversarial gaps and clock boundaries.
3. Obtain **two or more consecutive immutable atomic market+terms hours** before any source-continuity claim; subsequently authenticate position-specific funding, native fee tier, and execution costs before economic replay.

No Frozen, paper-results or dashboard champion mutation is authorized by this document.
