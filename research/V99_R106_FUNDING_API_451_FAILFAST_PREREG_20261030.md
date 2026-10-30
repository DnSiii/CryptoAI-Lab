# V99 R106 — source API 451 permanent-blocker handling (2026-10-30 05:41 BRT)

## Evidence before implementation
The first-party Binance funding API/archive run [41022012584](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41022012584) completed on 2026-10-30 04:58 BRT with **HTTP 451 on all 16 attempted 90-day windows (8 BTC, 8 ETH)**, **0 API events**, **0/1,983 rate-matched events per asset**, and independently verified **44 original publisher SHA256 ZIPs** and **1,983 unique nominal 8h slots per asset**. The raw original archive has only **821 exact 8h timestamps** and **1,162 offsets 1–31 ms**, which remains an unresolved timestamp-semantics distinction. Workflow SUCCESS is *not* a successful funding API corroboration or economic result.

## Fixed change and acceptance before implementation
- Treat HTTP **451** as non-transient restricted access for this runner. Do not retry a 451, and stop later API windows for the same symbol after the first 451. Do not bypass the restriction via proxy or alternative geo endpoint. Preserve 429/timeout retry behavior.
- Record separately the **planned** (8 per asset) and **actually requested** API windows (1 per asset under the same 451), with explicit machine-readable 'HTTP_451_ACCESS_RESTRICTED' error. This must **not** be reported as 1,983 absent market events.
- Keep original publisher SHA256 checks, TRAIN-only boundary, 1,983 original slots, all five chronological folds, strict original exact-grid gate (821), and no raw datasets in public artifacts unchanged.
- Extend independent oracle to check planned/attempted counts, and require a genuine 451 terminal error before accepting early termination; tampering with an early-stop report must fail.
- Test mocked HTTP 451, non-restricted error continuation, and independent oracle early-stop invariant without touching validation, holdout, Frozen, paper, legacy champion or orders. A source-only CI pass is **not** a full economic validation.

## Decision rule
With first-party funding API still blocked, report SOURCE_HOLD — HTTP_451_ACCESS_RESTRICTED, 0/1,983 API matches, **NO PROMOTION**. Official publisher ZIPs provide public source rates but **do not establish private account-settled funding, historical native fee tier, size-aware executable fills or strategy PnL**. For I1 separately, the licensed original Deribit BBO/size/mark/expiry tape remains 658/661 days missing, with 0/180 certified option lifecycles.

**Alternative:** an independently authenticated historical first-party API snapshot or venue-signed account funding statement with source provenance and lawful access, without attempting to evade 451. This change reduces repeated futile network requests and makes the actual blocker explicit; it does not unlock an engine.
