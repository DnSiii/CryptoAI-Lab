# V99 R106 I1 — original source + signed 661-day native bridge result (2026-10-31 23:50 BRT)

**Decision: SOURCE HOLD / NO PROMOTION. Not a validated economic engine.**

## Concrete critical-path implementation

Preregistered first in commit `17008ef4`. Added `research/tools/v99_r106_i1_signed_original_train_bridge.py` to combine two formerly disconnected execution paths: (1) original causal signal, all 661 original daily quote manifests, 180 original-intent decisions, original source-driven full entry books and held-contract event spine, independent market/numeric oracles; then (2) externally anchored Ed25519 whole-journal and every-event signed native replay, independently rechecked numeric report. Both severe and supersevere portfolios, chronological folds, six regimes, benchmark, tail concentration and max drawdown are compared by exact source-vs-signed numeric equality. A single immutable journal-byte snapshot prevents the source verifier and signed runner from consuming different caller-modified journals. No output on failure; existing output immutable.

**Important limitation:** this is an integrated **software verification path**, not a new candidate alpha, native fee/fill certification or a completed historical TRAIN. Original source and signed attestation archive-manifest identities have not yet been independently cross-pinned end-to-end by this bridge; do not promote or call source certification based on this integration. It is a prerequisite for a genuine licensed source run, not evidence that one has occurred.

## Actual CI and independent source run

- [GitHub Actions 41266748243](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41266748243) **SUCCESS**, 41/41 technical tests across five suites: 8 cost; 12 signed event source; 8 signed 661-day replay; 6 signed CLI; 7 joined source+signed bridge. The bridge tests use synthetic inputs and mocked external attestations; real temporary Ed25519 test signatures in other suites are not exchange receipts.
- Earlier CI [41266668281](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41266668281) failed on a Python syntax error in a snapshot patch; fixed in `e9e5f37` and confirmed successful above. No hiding failed run.
- Actual archived-source reexecution in successful CI: **182 causal signal observations, 132 positive, 0/182 signal/source intersections, 0 source-ready asset-weeks, 0 complete native economic lifecycles**, independently reconciled with original bytes. No economic TRAIN, no ROI, no certified orders or fills.
- Commit comparison `17008ef4..e9e5f37`: only bridge module, its adversarial tests and the existing source-gate CI workflow changed. Frozen, V16, V99 Frozen, paper-results, champion, validation, holdout and order paths untouched.

## Exact external blockers and permitted alternative

Original licensed Deribit BTC/ETH option BBO/size, venue and arrival clocks, complete 2021-12-09..2023-09-30 daily lifecycle and expiry/delivery records remain missing (**658 of 661 days**). Also missing: dated account-specific native fee tier, contract lot and unit schedule, margin/liquidation/settlement terms, execution/fill provenance, vendor capture completeness and independent auditor key/signatures anchored outside the repository. A self-declared JSON manifest, historical marks or modeled severe costs cannot replace those documents.

Next real step: obtain **authorized original 2022-01-23 24-hour BTC+ETH option quote sample** plus dated native contract/account terms and explicit license/coverage statement, verify the full open/mark/settle lifecycle and provenance, then acquire full TRAIN coverage only if the sample passes. CoinAPI/Tardis/Amberdata or equivalent licensed provider may be used with verified entitlement; no purchase or secret sharing authorized. Then cross-pin source manifest into signed attestations and run complete independent native economics/gates; sealed validation [2023-10-01,2024-01-18) and final holdout >=2024-01-18 remain unopened until formal freeze and permission.

**NO PROMOTION; NO ORDERS; NO PAPER CHANGES; NO UNVERIFIED PNL.**
