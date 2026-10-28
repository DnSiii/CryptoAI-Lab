# V99 I1 — native event -> 661d TRAIN equity bridge: execution result (2026-10-28 03:53 BRT)

**Decision: SOURCE_ONLY/HOLD — NO PROMOTION.** The research-branch native-coin event-to-equity bridge is **implemented and exercised**, but original historical options economics are **not** certified. Do not describe this as a profitable historical strategy or a complete validated V99.

## Actual implementation and GitHub execution

- Ex-ante preregistration: commit `76f68a0013ee1b667efd92bf32e2d23f62c57cf6`, before implementation.
- New executable bridge: `research/tools/v99_r106_i1_native_event_equity.py`, with tests `research/tests/test_v99_r106_i1_native_event_equity.py` and workflow `.github/workflows/v99-r106-i1-native-event-equity.yml`.
- Final run: **[Actions 40646513724](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40646513724)** on `4651acd1910e320ef921e2f34aff39309488f67f`: **SUCCESS; 9/9 tests passed**, preregistration ancestry checked; explicit nonfixture economic gate refusal observed: `BLOCKED_ORIGINAL_ECONOMIC_SOURCE_PROVENANCE_NOT_CERTIFIED`.
- Reconstructed **661 daily TRAIN clocks per scenario** from native BTC/ETH coin wallets. Scenario-specific severe/supersevere entry/exit/settlement fee floors are enforced. Actual exposure keys come from open positions, never user-supplied equity. OPEN requires the fixed Monday t-1 signal and deterministic 28–35d two-strike selector, and at most **one** position per asset-week. MARK requires the same original contract pair and fresh same-clock quote, all held positions marked for each end-of-day NAV. SETTLE_BATCH uses the contractual expiry clock, atomic due positions, index and fee floors. No capital-injection event exists.
- Regression controls rejected fabricated credit, missing daily marks, altered source indices, differing severe/supersevere market index paths, understated scenario fees, duplicate asset-week openings, sealed timestamps and nonfixture promotion. The complete synthetic single-vertical journal produced **1/5 positive folds** under each cost scenario and **failed** the existing preregistered numeric fold gate. This is a **synthetic accounting fixture**, not an original market result or an alpha rejection/promotion.

## What is and is not now functional

The accounting **internal gap** between native event journal and 661d numeric risk screen is reduced: a 661-day ledger is now derived from BTC/ETH wallet cash, open liabilities and original-index *input* rather than an arbitrary supplied USD NAV. This does not establish original quote provenance, original fills, historical fee tier, margin/maintenance/liquidation, settlement index or benchmark. A caller may supply `fixture=false` for **provisional, uncertified computation only**; the official numeric economic gate still rejects it until independent original-source verification exists. Do not label that output TRAIN, realized paper or ROI.

**Actual original coverage: 0/180 fixed asset-week complete lifecycles certified.** No historical nonfixture run or new original ROI was produced. Frozen V16/V99, legacy champion, paper/results and validation [2023-10-01, 2024-01-18), final holdout >=2024-01-18 were untouched. No orders.

## Remaining blocking dependency and fastest next justified step

Obtain lawful, original, complete Deribit BTC+ETH options bid/ask **and sizes** with venue/arrival clocks and same-contract daily holding through contractual settlement for 2021-12-09..2023-09-30; original dated account fee-tier/settlement fee, contract unit, inverse-coin margin/maintenance/liquidation and delivery-index receipts; and independent quote/fill replay. Source files must be hashed, coverage gaps independently verified, and each event bound to those bytes. The local import path and original signal replay already exist. **Do not** mistake a paid entitlement, self-declared manifest, synthetic quote, a GitHub SUCCESS or modeled cost floor for those receipts.

Candidate lawful supplier path: verify Tardis invoiced five-year OPTIONS entitlement or equivalent Amberdata archive *before any purchase*. Existing Actions `TARDIS_API_KEY` probe previously found no configured key; no vendor archive was downloaded. On receipt, connect original byte-verified quotes and dated native terms to the event journal, independently reconstruct all 661 daily wallets and 180 asset-week decisions, run the fixed numeric gates, and reject/freeze based on original TRAIN. Do not open sealed validation unless a brand-new candidate passes original TRAIN and is formally frozen.
