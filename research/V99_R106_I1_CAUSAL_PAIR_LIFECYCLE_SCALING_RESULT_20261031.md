# V99 I1 — causal held-pair source screen scaling: verified (2026-10-31 16:48 BRT)

**SOURCE-ONLY / NO PROMOTION. No economic TRAIN, ROI, historical execution or new source days.**

Preregistration: [source-only fixed rules](V99_R106_I1_CAUSAL_PAIR_LIFECYCLE_SCALING_PREREG_20261031.md), committed at `faf177030d0c71b97ec45ea053cf59f6e808d3be` before implementation.

## Concrete changes and evidence
- Replaced the quadratic held-contract causal-pair existence scan in `research/tools/v99_r106_i1_lifecycle_daily_tape.py` with an arrival-clock ordered <=1s window, a sorted venue-clock index, and exact numeric-strike exclusion.
- The independent original-byte oracle uses a **different venue-clock ordered** <=1s sweep and an arrival-clock index, without importing the primary implementation.
- Added five synthetic tests, including 1,380 randomized differential comparisons against the original brute-force reference (46 input sizes x 30 deterministic cases per size), exact inclusive 1s and 1s+1us exclusions on both clocks, numeric-strike aliases, 6,000 distinct strikes with no synchronized venue clocks, and 6,000 aliases of one numeric strike.
- [GitHub Actions 41235816557](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41235816557) **SUCCESS** at commit `1936f1f767dde3139ad02c729dfdc8989b8e0aac`. All 5/5 differential tests passed in 0.118s in CI; the existing full 661-day **synthetic** lifecycle and independent replay, including causal entry, revoked books, 35d8h expiry, and forged-source controls, also passed. This is a software equivalence check, not an original-data economic run.
- Compared base `003a87d` to `1936f1f`: exactly 5 files changed (preregistration, two source-screen modules, tests, CI). No model parameters, economic thresholds, frozen artifacts, paper or sealed partitions changed.

## Blocking dependency and decision
The source-side pair scan is now less dependent on quadratic symbol comparisons, but no throughput claim on a paid real archive is made. **658/661 original Deribit option days remain absent, 0/180 complete option lifecycles certified.** Missing authorized 2022-01-23 nonsample 24h BTC/ETH quote+size+two-clock tape and dated written entitlement/vendor provenance; alternatively a licensed independently authenticated equivalent source. Full 661-day historical tape, dated native contract/fee-tier/margin/delivery evidence and independently authenticated execution/settlement are still mandatory before a full economic TRAIN. No validation [2023-10-01,2024-01-18), final holdout >=2024-01-18, Frozen, champion, paper or orders accessed.

**Decision: SOURCE HOLD — NO PROMOTION.** No strategy selected or retuned.