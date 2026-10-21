# V99 R106 D1 — C121 full local source suite and scenario divergence (2026-10-21 BRT)

Decision: **DATA_ONLY/HOLD — NO PROMOTION**. D1 remains a preregistered, unproven spot/perpetual basis-carry architecture; no authenticated economic TRAIN was run, no sealed validation or final holdout was opened, no real orders or paper results were changed.

## Fresh remote read
Branch `research/v99-r106-native-all-regime-engine` still points to `4d7a46bed30bfa5de95a310915b4623611a6939e`; last branch GitHub Actions run `39128800765` (2026-10-18 12:48 UTC) was a synthetic calendar preflight, not an economic TRAIN. No new remote CI.

## Actual local execution
Unmodified C118/C120 source snapshot: **985 pytest passed, 5 skipped, 1 deselected, 120 subtests passed, zero failures** in 204.03 s using `python -m pytest -q research/tests -k 'not full_calendar'`. This is local software verification only; the explicitly excluded full-calendar test was not run in this command.

Independent 240-hour deterministic integration replay, for each severe/supersevere scenario, verified 3 daily decisions, 60 modeled settlement events, 239 intrabar risk hours and complete synthetic calendar. At +0.25% per 8h synthetic funding, severe selected positions on 3/3 decisions while supersevere stayed cash 0/3; at +0.50% per 8h both selected 3/3; at +0.01% both stayed cash 0/3. These are intentionally unrealistic controlled fixtures, **not measured OKX rates, economic returns or real execution**. This demonstrates cost-dependent exposure, not superior supersevere alpha.

241 staged add-only files were independently rehashed against the C118 release manifest: 241/241 SHA-256 matches, 1,173,562 bytes, zero missing; six remote conflicts remain protected. No source published.

## Economic and publication block
Frozen D1 requires projected 24h funding strictly >0.56% severe or >1.12% supersevere, based on 3 previously settled 8h fixes, before basis/risk/cost checks. No authenticated 2021-12-09 to 2023-10-01 first-party spot/perp prices, historical native fees, settled account funding, or actual fill receipts were available locally. Consequently no 5-fold economic ROI, benchmark superiority, 3x2 regime robustness or independent actual-execution certification is possible. C1/C2 remain permanently rejected. Never use synthetic tests to promote.

Next: integrate source with six conflicts resolved through authorized review, run/poll remote CI, collect authenticated native TRAIN inputs, execute preregistered D1 economic TRAIN with independently replayed hourly account and severe/supersevere paths. Hold validation [2023-10-01,2024-01-18) and final holdout >=2024-01-18 sealed until formal gates. Preserve immutable V16/V99 Frozen, paper and champion.
