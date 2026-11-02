# V99 I1 — Original CoinAPI source mutation after independent replay (2026-11-02)

Scope: TRAIN-only source-integrity correction; no alpha tuning, no synthetic economic claims, no validation/holdout, Frozen, paper or orders.

Observed internal risk: the 661-day CoinAPI chain verifies each compressed original SHA-256 before invoking the independent byte replay, but does not verify that the same original bytes remain unchanged after that replay. A replacement after the independent verifier returns can evade the per-day gate, especially for the final file/day. The signed/source bridge must not treat such an unstable archive as trustworthy.

Fixed before implementation: retain the initial SHA-256 verification, then rehash every original partition of the day after the independent derived-byte oracle and before accepting daily row/coverage results. Raise deterministic COINAPI_ORIGINAL_BYTES_CHANGED_DURING_REPLAY on mismatch. Apply to fixture and licensed nonfixture inputs; do not alter market data, historical partition, economics or immutable artifacts.

Negative control: construct the existing 661-day synthetic original/derived chain, allow the independent oracle to complete the first day, mutate one original gzip in-place immediately after the oracle returns, and assert the chain rejects it. Restore original bytes and confirm ordinary mutation/rights fail-closed gates remain intact. Trigger the existing original-byte-chain CI on the research branch and inspect its run. Source-integrity testing only, not a complete engine or economic validation.