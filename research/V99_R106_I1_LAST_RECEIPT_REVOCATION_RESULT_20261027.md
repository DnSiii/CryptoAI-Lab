# V99 I1 — last original receipt revocation: CI result (2026-10-27 19:50 BRT)

**Decision: SOURCE_ONLY/HOLD — NO PROMOTION.** This is a source-integrity fix, **not** a working or validated economic engine. No original licensed 2021–2023 Deribit BTC/ETH options archive was obtained. No historical ROI, real fills, five-fold economic TRAIN, validation, holdout or orders.

## What was actually changed and independently checked

- Preregistered at [2a4ed08](https://github.com/DnSiii/CryptoAI-Lab/commit/2a4ed08557ce660d718b52eab7947f7439018d20), before the code changes.
- The original 661-day source scanner now honors the **last arrival-ordered original receipt for each exact option contract on each day**: a newer invalid/zero-sized/stale quote revokes a previous valid daily contract mark. The weak *any valid market row* counter is explicitly unchanged and cannot certify a held position.
- The Sunday <=300s before Monday decision causal entry quote now also expires on a newer invalid original receipt. The independently implemented oracle recomputes both from the original hashed day files, without importing the primary scanner.
- The synthetic 661-day GitHub workflow asserts positive **1/180** causal Sunday+held-contract source pair; a later invalid Sunday quote revokes causal eligibility to **0/180** while preserving the weak held-contract count **1/180**; a later invalid Monday quote revokes exact-contract continuity to **0/180**. Original forged-count and skew adversarial checks also run. These are **synthetic source checks**, not economic opportunities or returns.

## Execution evidence

- [GitHub Actions 40597603672](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40597603672): **SUCCESS**, head `331b747f600dd4da12cc8c65d4e368c51717c7c8`, including the full synthetic 661-day streaming replay and independent oracle.
- [Scope diff](https://github.com/DnSiii/CryptoAI-Lab/compare/cb14d41c985d4ad4ee70d11762f5696484e10a91...331b747f600dd4da12cc8c65d4e368c51717c7c8): exactly preregistration, primary scanner, independent oracle and CI synthetic checks. **No Frozen, paper, champion, order, or sealed-period path changed.**

## Remaining critical path (external, verified absent)

0/180 **historical complete certified** BTC/ETH option lifecycles. Need licensed historical original options BBO+sizes with exact contract IDs, venue and arrival timestamps and 28–35-day lifecycle continuity through expiry; authenticated original delivery/settlement index and dated account-specific maker/taker/settlement fees, native margin, collateral and liquidation terms. The `TARDIS_API_KEY` secret was absent on the last authenticated probe. A verified Deribit-options-specific 5-year invoiced entitlement or an independently licensed equivalent source is acceptable, but no access, price or coverage has been purchased/confirmed. Without these bytes and dated native terms, an honest complete severe/supersevere five-fold TRAIN and independent economic replay cannot run. Validation from 2023-10-01 and final holdout >=2024-01-18 remain sealed.

**Next useful step:** source license + historical receipt acquisition and verified integration into the native accounting/economic TRAIN; stop substituting synthetic source checks for a validated engine.
