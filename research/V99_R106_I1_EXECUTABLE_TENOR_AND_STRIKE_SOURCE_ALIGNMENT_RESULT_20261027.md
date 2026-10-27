# V99 I1 — executable-tenor and economic-strike source alignment: CI result (2026-10-27, 20:49 BRT)

**Decision: SOURCE_ONLY/HOLD — NO PROMOTION.** This is a material necessary-source eligibility correction, **not** an economic TRAIN, fill, profitability test, native fee/margin attestation, or completed trading engine.

## Executed correction, precommitted before implementation

- Preregistered at [420fd6d](https://github.com/DnSiii/CryptoAI-Lab/commit/420fd6db1fd712e0ad909a9c41481cd2abccff23), before any code.
- Original I1 source scanner and independent oracle now align with the **unchanged** native I1 engine's option expiration at **08:00 UTC** and exact **28d <= expiry - Monday 00:00 UTC <= 35d**. A Monday+35 *calendar day* expiry actually has **35d8h** remaining and is NOT eligible for that Monday. The existing 90-Monday TRAIN decision schedule is unchanged.
- Two original contract symbols are not a valid source pair unless they have **different positive numeric strikes**. Symbol aliases `27000` vs `27000.0` must not count as a two-leg vertical. The oracle recomputes these checks independently from original hashed synthetic source files.
- The independent 661-day adversarial test correctly distinguishes **2021-12-13** (2022-01-17 expiry is 35d8h and therefore excluded) from **2021-12-20** (the same expiry is 28d8h and therefore potentially eligible). No future data was used to make a trade decision.

## Real GitHub execution

- [Actions 40604599966](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40604599966), final source commit [df0e4d6](https://github.com/DnSiii/CryptoAI-Lab/commit/df0e4d603d9121bb1822e34e965086fc0082f0ec): **SUCCESS**, all workflow steps green, including independent replay and adversarial tests.
- On **explicitly synthetic** 661-day data: legacy weak presence 182/182; fixed 28–35d weak presence 180/180; default changing-contract fixture **0/180** exact held pairs; valid positive control **1/180** held and causal pair; same-economic-strike aliases and Dec-13 35d8h over-tenor vetoed; skewed/revoked Sunday books and invalidated Monday held books vetoed. These are **source-integrity counts, not trading opportunities, fills or ROI**.
- Interim GitHub runs failed while correcting test fixture scoping and manifest SHA restoration; the **final** run above passed. [Scope diff from prereg to final](https://github.com/DnSiii/CryptoAI-Lab/compare/420fd6db1fd712e0ad909a9c41481cd2abccff23...df0e4d603d9121bb1822e34e965086fc0082f0ec) modifies only the source scanner, independent oracle and dedicated CI fixture. No Frozen, paper, champion, order path, validation or holdout was touched.
- Deribit [current official inverse-options documentation](https://support.deribit.com/hc/en-us/articles/31424939096093-Inverse-Options) confirms 08:00 UTC expiry; this contemporary page **does not by itself certify 2021–2023 historical margin, fee or contract terms**.

## Still blocking genuine economic delivery

**0/180 historically certified complete BTC/ETH option lifecycles.** No lawful authenticated full 2021-12-09..2023-09-30 Deribit option BBO+sizes tape with original venue/local arrival clocks and continuous exact-contract entry-to-expiry records; no original dated account-specific fee/delivery tier, inverse-coin margin/maintenance/liquidation terms and independently bound delivery-index/fill provenance. The previous authenticated Tardis and CoinAPI probes had no usable license credentials. The licensed source must be obtained and independently SHA/source-attested (Tardis option-specific entitlement, Amberdata, or equivalent) before complete five-fold severe/supersevere 3x2-regime economic TRAIN, independent replay and formal gates. No validation >=2023-10-01, final holdout >=2024-01-18, paper, Frozen, or orders.

**Next critical path:** acquire and bind original historical data + dated native cost/risk terms; run the single fixed I1 integrated economic TRAIN with independent accounting, then reject/freeze only by preregistered gates. No PnL claim and **NO PROMOTION**.
