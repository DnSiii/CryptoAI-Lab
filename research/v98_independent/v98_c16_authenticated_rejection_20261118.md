# V98 C16 — authenticated replay decision (2026-11-18)

**Decision: REJECTED, no promotion.** This decision applies to the preregistered C16 complete seven-slot architecture, not an invitation to retune its sign/windows/cost assumptions. No holdout or V14/V15/V99 comparison was used.

## Evidence
- GitHub Actions run [44439568960](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/44439568960), head `5fdd8265af9ade35fb8382849fb01e866d0db755`, succeeded with pinned authenticated Clean-4 source manifests and native funding. Artifact `14490935834` (`v98-independent-c16-unvalidated-44439568960`) contains the summary, independent audit, and three 27,047-row ledgers.
- Price manifest SHA-256 `01e7bdeb8bcaf34ee898e322cf20f4479c0e25a9066b40f8cd2446286259f8a8`; funding manifest SHA-256 `f33094dfc065aa862a529d46f36e15f8a418ab085780214a0423488d2ff49622`.
- From initial US$10,000: final equity **US$20,340.67 (1x)**, **US$17,927.78 (2x)**, **US$13,902.90 (4x)**. Max drawdowns: **24.75%, 25.31%, 28.92%**. Ledger audit reports `arithmetic_reconciled=true` for all three cost scenarios. These are in-sample research results, NOT an independent future holdout.
- Yearly net return 1x: **2023 +79.69%, 2024 +12.00%, 2025 +1.07%**. At 2x: **+70.99%, +11.21%, -5.72%**. At 4x: **+48.65%, -2.73%, -3.85%**.
- Independent second-pass diagnostic on 4x ledger: 2023 turnover **60.46**, 2024 **76.41**, 2025 **35.96**; 2024 cost-return sum **0.1834** vs gross-return sum **0.2298**, and funding-return sum **-0.0341**; 2025 gross-return sum **0.0613**, cost-return sum **0.0863**, funding-return sum **-0.0052**. Sums are arithmetic return components, not compounded PnL.

## Gate and causal diagnosis
The preregistered 4x-cost validation criterion fails in **both 2024 and 2025**, despite positive development performance in 2023. C16's high 2024 turnover and weak 2025 gross edge do not sustain compounded growth after realistic stress costs. The economic failure is sufficient for rejection; no need to spend an additional full-history replay on cosmetic modifications or retrospective sleeve ablations. Passing arithmetic reconciliation is not evidence of profitable forward performance.

**Next distinct hypothesis:** before implementation, preregister a structurally different complete-system design emphasizing materially longer holding periods / sparse event-driven allocation to reduce fee drag while preserving asymmetric growth participation. Validate 2023 development then 2024/2025 separately; if either validation year is consulted during redesign, mark it research-contaminated and require an untouched future holdout for any subsequent promotion. No 2026+ access during training. Preserve XRP quarantine, Phase083 exclusion, Frozen and paper.
