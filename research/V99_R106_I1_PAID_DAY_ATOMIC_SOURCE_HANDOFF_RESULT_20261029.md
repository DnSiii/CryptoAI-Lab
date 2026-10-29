# V99 R106 I1 — atomic paid-day transfer -> independent source gate, external digest veto (2026-10-29 19:49 BRT)

**Decision: SOURCE_ONLY/HOLD — NO PROMOTION.** This is a software critical-path closure, **not** acquired Deribit data, historical economic TRAIN, native fill, PnL, ROI, validation or paper.

## Concrete defect repaired

Previously a lawful 2022-01-23 full-universe OPTIONS quote gzip could be downloaded and marked as successfully transferred after 24/24-hour BTC/ETH presence without automatically evaluating the fixed 2022-01-24 Monday 28–35d synchronized two-strike put source gate. That left a manual decision and risked purchasing the remaining 658 historical days on mere file presence. The transfer also computed a local SHA256 but did not accept or enforce an **independently supplied vendor digest** before atomically publishing the paid archive.

Preregistered **before** respective changes at commits [0685330](https://github.com/DnSiii/CryptoAI-Lab/commit/06853303579f6652d3ff793b4782153b9ef6d56c) and [ec50342](https://github.com/DnSiii/CryptoAI-Lab/commit/ec50342b94ef97a7349773c3b407ce9999d8056c). Changes:
- [36a3fdb](https://github.com/DnSiii/CryptoAI-Lab/commit/36a3fdb7972e9ebcf8166ca03993f61428cba97d): for **only** the fixed one-day authorized `2022-01-23` transfer, invoke the existing independent compressed-byte feasibility replay after transfer or immutable existing-day reuse. Explicit `SOURCE_FEASIBLE_ONLY_NOT_ECONOMICS` versus `SOURCE_VETO_NOT_LOSS`; neither certifies economic profitability.
- [abde6d3](https://github.com/DnSiii/CryptoAI-Lab/commit/abde6d3a969a01a817e27a4a3beedc72f09a3e09): optional independently provided lowercase 64-hex `--expected-sha256` only for this preselected day. Reject malformed/wrong-day digest **before network**, compare original compressed bytes **before** immutable publication, refuse mismatched existing bytes without overwriting, and pass the same digest to the independent replay. If no independent vendor digest is supplied, `external_sha256_matched=false`; a locally computed digest is not independent proof.
- [67fe2fe](https://github.com/DnSiii/CryptoAI-Lab/commit/67fe2fe8353c90bf07c43e7fbc17e06beaaf2220), [53541ea](https://github.com/DnSiii/CryptoAI-Lab/commit/53541eaf30b5c6982ac27c0a40d5d609a568d0d7) and [761a36e](https://github.com/DnSiii/CryptoAI-Lab/commit/761a36e6db82a10d5189baac07c15678ce6d4680): adversarial transfer/source-gate/digest tests and elimination of flaky recompression-byte comparisons. Workflow verifies both prereg commits are ancestors.

## Executed GitHub CI and independent verification

[**Actions 40968559498 — SUCCESS**](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40968559498), final commit `761a36e`: **15 importer + 22 licensed-transfer + 8 independent one-day source tests = 45 offline tests PASS**. Both mocked outcomes (no eligible pair -> source veto; 1 BTC + 1 ETH eligible pairs -> feasibility only) passed. Wrong digest blocks publication and existing reuse; wrong scope/format blocks network; independent original-byte replay and 24h capture gates pass only on synthetic test inputs.

The same final CI **actually** checked for the nonfixture paid source and full licensed archive, obtaining:
- `BLOCKED_LICENSED_2022-01-23_SOURCE_DAY_NOT_DELIVERED`
- `BLOCKED_ORIGINAL_LICENSED_661_DAY_OPTIONS_ARCHIVE_MISSING`

These are actual missing-source results, **not** market economics. Independent read-only GitHub compare from pre-cycle `1413db81` through `5b7c032` showed changes only in local transfer, tests, workflow and prereg docs; subsequent `761a36e` touched only the test. Frozen V16/V99, legacy champion, paper/results, validation [2023-10-01,2024-01-18), final holdout >=2024-01-18 and order paths were not modified.

## Exact procurement contract, alternative and hard boundary

The fixed sample is **2022-01-23 00:00–24:00 UTC**, full BTC+ETH Deribit OPTIONS `quotes`, followed by the **2022-01-24 00:00 UTC** frozen decision. It requires a dated lawful written license and retention grant, authenticated full-universe key/entitlement, original gzip, independently attributable vendor SHA256, two original clocks, positive bid/ask and size, and independent gap/universe evidence. [Tardis downloadable CSV documentation](https://docs.tardis.dev/downloadable-csv-files) explicitly says CSV datasets omit disconnect events; 24/24 hourly quote presence is only a necessary heuristic. [Tardis raw HTTP API](https://docs.tardis.dev/api/http-api-reference) includes disconnect markers and can serve as an alternative gap-evidence source, subject to licensing. [Tardis options_chain schema](https://docs.tardis.dev/downloadable-csv-files/data-types) includes underlying-index/price and marks for separate verification but **does not certify native delivery settlement**. Equivalent independently licensed original source is acceptable.

The fixed one-day sample can only establish source feasibility; no retrospective reranking after its inspection. Full economic TRAIN still lacks **658/661 historical original days**, native dated contract/lot size, account fee tier, delivery-index/settlement, coin margin/liquidation, independently modeled size-aware fills and full 5-fold severe/supersevere accounting. **0/180 economic lifecycles certified**; no ROI, no model promotion, no paper claims, no orders.

**Next justified action:** obtain the lawful original **single-day** vendor archive + independent digest/gap evidence; run the already integrated fail-closed source gate before any full-history acquisition. If a source veto occurs, do not purchase 658 days for this fixed I1 on the assumption of executable pairs; prioritize a separately preregistered distinct architecture with obtainable native sources instead.
