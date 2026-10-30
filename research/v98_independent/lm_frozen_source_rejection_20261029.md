# V98 LM — permanent source-only rejection, 2026-10-29

**REJECT LM; NO RESCUE, NO PNL, NO HOLDOUT, NO PROMOTION.**

Preregistered architecture frozen in commit 02ddab5e700ca5c2289e7065ae27f20aae3e0cd0 before implementation f8244a9ef65e8c74625750df9e7d71fba7cf4681. Authenticated pinned artifact 12549265452: exactly 18,288 1h bars per Clean-4 asset and 9,144 native signed funding/mark-bound events. SHA256 validation passed using the existing V98 source reader. December 2022 warmup, 2023/2024 training only; no 2025/2026+, XRP, Phase083, V14/V15/V99 internals, Frozen or paper.

Independent entry replay against the separately implemented LM source returned **zero entry mismatches**; synthetic causality and authenticated future-prefix mutation passed; no silent updates, invalid quote entries or intended gross breach (maximum 0.76).

| Year | Opportunity | Relative Value | Stress/Recovery |
|---|---:|---:|---:|
| 2023 | **7** | **4** | **6** |
| 2024 | 11 | **6** | 8 |

Preregistered minimum is 8 starts **per sleeve in each year**. Four hard source-gate failures. **No economic PnL was computed**, because source eligibility failed. The LM candidate is permanently rejected; do not adjust thresholds/clocks/expiry to rescue LM. No claim of 30-cell settlement, independent ledger, validation or benchmark superiority. Next pursue a genuinely distinct architecture, not LM variants.

The signed funding source uses conservative mark bounds; policy receipt explicitly states `api_mark_attested=false`. That distinction remains an external provenance limitation and must not be called native API mark attestation.
