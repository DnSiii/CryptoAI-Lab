# V99 R106 I1 — target-day entitlement critical-path correction, executed 2026-10-29 17:52–17:53 BRT

**SOURCE_ONLY/HOLD — NO PROMOTION. No original paid archive, economic TRAIN, ROI, validation, holdout, paper or orders.**

## Concrete defect and fix
The previously built opt-in Tardis transfer unconditionally invoked `_scope_covers_train` (requires a full 2021-12-09..2023-10-01 options grant) even for the **single already-preregistered 2022-01-23 UTC source-day** request. This would reject a legitimate limited one-day paid evaluation grant and force a 661-day purchase before a one-day feasibility check. This was a **local preflight software blocker**, not proof that a vendor grant exists.

Pre-implementation preregistration [9173054](https://github.com/DnSiii/CryptoAI-Lab/commit/9173054dd4770975effd84e5d31acc2ee389563c). Implementation [1df58c0](https://github.com/DnSiii/CryptoAI-Lab/commit/1df58c0225de5fc24ee2948d8483ae0e887a9b63) and [01f96ae](https://github.com/DnSiii/CryptoAI-Lab/commit/01f96ae800121cb15cffd42842b83276fa6e4f75). Negative-control tests [9149239](https://github.com/DnSiii/CryptoAI-Lab/commit/91492393a2e5f9b6ac01492175ac1e8de490f8d8).

- **Only local opt-in transfer** now requires original `api-key-info` grant to cover the *exact requested* UTC interval, with Deribit exchange, explicit options-inclusive plan and complete `OPTIONS` group or all-symbol wildcard. A one-day grant cannot authorize any adjacent day, finite partial-symbol grants, or full TRAIN.
- Existing separate full-history entitlement probe is **unchanged**; it still requires full TRAIN access. Local transfer still requires `--execute`, nonempty local written license evidence, authenticated key, safe path, no overwrite, 24/24 BTC+ETH hourly original quote presence and gzip/CSV integrity. No vendor document is automatically legally certified.
- The fixed source target remains **Sunday 2022-01-23 00:00–24:00 UTC**, followed by Monday 2022-01-24 00:00 TRAIN decision. No re-ranking after any market bytes.

## Actual CI and independent negative evidence
[GitHub Actions 40952802235](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40952802235) **SUCCESS** at commit `91492393`: 15 synthetic local 661-day importer tests + 18 offline licensed-transfer tests passed. New adversarial checks confirm one-day 2022-01-23 mock grant accepted; neighboring-day/two-day requests, wrong venue, partial symbol list, naive/short grant denied **before any source download**. CI separately verified that the real licensed 661-day local archive is absent, printing `BLOCKED_ORIGINAL_LICENSED_661_DAY_OPTIONS_ARCHIVE_MISSING`. The simulated bytes are not real market data.

[GitHub Actions 40952767184](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40952767184) **SUCCESS** on the independent full-TRAIN entitlement probe: 16 offline tests passed, but the **actual** authenticated probe printed `BLOCKED_NO_AUTHENTICATED_ARCHIVE_KEY_CONFIGURED` (`scope_endpoint_http=null`, no paid archive probes). A green workflow is **not** source/economic certification.

## Binding next action and precise external dependency
Request from Tardis or independently attributable equivalent vendor: **dated written lawful license/retention permission for the 2022-01-23 24h BTC+ETH Deribit OPTIONS quote universe**, matching authenticated vendor OPTIONS full-universe grant, original 24h `OPTIONS.csv.gz` bytes, SHA256, both original event and local arrival timestamps, bid/ask prices and sizes, vendor gap/universe completeness attestation. For the real local transfer, configure a lawful `TARDIS_API_KEY` privately and use explicit `--start-date 2022-01-23 --max-days 1 --execute --license-evidence ...`. No key, license or paid bytes were supplied during this run, so **no actual one-day transfer** was attempted. A verified one-day tape can establish only a necessary source feasibility gate; it cannot validate profitability.

Full I1 original economic TRAIN remains blocked by **658/661 missing historical original days**, historical native account fee tier/contract sizing, coin margin/liquidation and delivery-index settlement evidence, conservative size-aware execution and independent five-fold severe/supersevere accounting. **0/180 option lifecycles economically certified.** Alternative: independently licensed equivalent complete archive, or a distinct economically justified architecture with fully obtainable native evidence. No retuning rejected C1/D3, no posthoc strategy selection, no sealed data access.

Frozen V16/V99, legacy champion, paper/results, validation [2023-10-01,2024-01-18) and holdout >=2024-01-18 unchanged.
