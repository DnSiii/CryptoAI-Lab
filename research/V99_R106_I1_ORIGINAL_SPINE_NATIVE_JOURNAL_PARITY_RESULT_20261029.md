# V99 R106 I1 — original held-contract source spine/native journal parity: implemented and independently CI-verified

Date: **2026-10-29 09:47 BRT**. Decision: **SOURCE_ONLY/HOLD — NO PROMOTION.** This is an INTERNAL source-to-accounting execution-path correction, not a trading alpha, original economic TRAIN, certified fills or realized PnL.

## What changed (preregistered before implementation)

Ex-ante registration: [0c054f35](https://github.com/DnSiii/CryptoAI-Lab/commit/0c054f35bee2fcc86baf9c4286cb1ab4d6b9a8a2).

- Added `research/tools/v99_r106_i1_source_spine_journal_parity.py`: reconstruct each severe/supersevere scenario's held-contract plan by running the **existing deterministic fixed vertical selector** on the full original OPEN book, compile the existing original 661-day OPEN/MARK/SETTLEMENT_DUE source spine, and reject any missing, extra or altered OPEN, held-contract daily MARK or expiry-due settlement **before** native NAV. Original bid/ask, source-size, venue/arrival timestamp and contract identity are compared. Scenarios may legitimately hold different positions because costs can change vetoes.
- Added a separately implemented independent oracle `research/verification/independent_v99_r106_i1_source_spine_journal_parity.py` that does **not** import the source-spine compiler: independently reconstructs each position's required 661-day chronological daily mark grid and exact expiry, checks journal coverage and claimed counts. No retune, no model selection, no sealed data.
- Integrated both checks before `replay(journal)` in `research/tools/v99_r106_i1_original_to_provisional_numeric.py`; added explicit adversarial tests for missing original daily MARK, missing settlement, and falsified production parity report. Updated existing GitHub CI to enforce preregistration and track both implementations.

## Actual GitHub CI and economic outcome

Final [GitHub Actions **40875995871**](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40875995871) **SUCCESS**, commit [f27c1d2](https://github.com/DnSiii/CryptoAI-Lab/commit/f27c1d2ce9e3e783c2c74f5fc18187e370c9390c). The run executed **7/7 source CASH-veto tests and 15/15 original-shaped synthetic 661-day integration/adversarial tests**. The independently implemented oracle correctly rejected missing MARK and settlement even when given a forged production parity report. These 22 tests are **software/fixture evidence only**.

The same run restored **182/182 archived actual causal signal rows**, bound **180 fixed BTC/ETH Monday intents (132 positive)**, then attempted the actual nonfixture original-to-numeric runner. It failed closed, **before NAV**, with exact blocker `ORIGINAL_661D_MANIFEST_NOT_DELIVERED` / `BLOCKED_ORIGINAL_661D_LICENSED_DERIBIT_OPTIONS_ARCHIVE_NOT_DELIVERED`. **0/180 original option lifecycles economically certified; no native economic TRAIN; no original ROI.** CI green means the missing source was correctly rejected, not that an economic strategy passed.

## Remaining exact external critical path

The I1 options mechanism still lacks **658 of 661 original Deribit BTC/ETH daily quote/size/arrival-clock archives**, an independently verifiable written historical-data license/entitlement and complete capture evidence. The first procurement gate is **one legally authorized nonsample full day** with original quotes/size/timestamps and dated terms. Then source all 661 days and separately authenticate historical underlying/settlement indices, native option lot/contract sizing, account-specific fee tier/delivery charges, coin collateral/margin/liquidation and conservative size-aware hypothetical execution (real historical fills for orders never placed do not exist). An independently verified equivalent vendor archive is an alternative, subject to identical completeness/clock/terms checks. No fabricated source substitution is allowed.

Tardis documents normalized daily historical Deribit quotes, with first calendar day of each month offered without API key; those free samples **cannot** substitute for all required days or establish full licensed coverage. The alternative CoinAPI documents historical Deribit options coverage varying by symbol; per-contract dates and quote/size/clock availability must be verified before purchase. Do not assert either vendor can supply the exact required original archive without a dated quote and sample.

## Binding decision

**SOURCE_ONLY/HOLD — NO PROMOTION / NO FREEZE / NO ORDERS / NO PAPER / NO VALIDATION / NO HOLDOUT.** No new strategy or serial feature search was launched; rejected C1, D1, D2, D3, E1, H1 remain rejected. Frozen V16/V99, legacy champion, paper/results, sealed validation [2023-10-01,2024-01-18) and final holdout >=2024-01-18 were not read or modified.

Next: obtain **the one authorized nonsample Deribit day and its dated license/contract specs** to exercise the now source-bound native event chain on real data; if procurement is unavailable, continue targeted integration on fixtures but do not claim economics or retune rejected systems.
