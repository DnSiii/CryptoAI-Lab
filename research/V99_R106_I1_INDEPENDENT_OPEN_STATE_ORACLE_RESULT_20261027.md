# V99 I1 — independent OPEN state oracle correction and original-source veto (2026-10-27 00:51 BRT)

**Decision: SOURCE_ONLY/HOLD — NO PROMOTION.** No economic TRAIN, ROI, orders, validation/holdout or Frozen/paper/champion/dashboard changes.

## Material correctness defect removed
Previous independent I1 fixture OPEN verification checked only coin cash, reserve delta, contract symbols and quantity. It could accept a forged state with changed contract expiry/strike, changed last clock, settlement history, marks, initial wallet coin or maintenance while reporting an independent match. Precommitted scope in `research/V99_R106_I1_INDEPENDENT_OPEN_STATE_ORACLE_PREREG_20261027.md` (commit `83c04b3`) **before** oracle change.

Implemented full independent fixture transition binding (commit `9e5cc13`): exact selected contract IDs/expiry/strikes, 1-lot quantity, unchanged initial coin/settlement history/marks, exact Monday decision clock, valid positive margin terms, cash/reserve conservation and immediate two-sided close liability including both scenario exit friction floors. Independent oracle now **requires explicit fixture margin inputs** for OPEN; still never certifies historical margin provenance. Added adversarial tampering cases (commit `737af09`).

## Real GitHub CI execution
Initial runs [40446279461](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40446279461) and [40446299326](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40446299326) failed at prereg ancestry because checkout fetched only ten commits, omitting the older prereg commit (log: `fatal: Not a valid commit name`). Corrected CI to deepen the shallow history only as needed, without full-repository fetch (final workflow commit `b5565e7`).

**Final [Actions 40446382592](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40446382592): SUCCESS**. 15/15 fixture tests passed, prereg ancestry verified, original archived receipts downloaded and original signal-to-options join plus independent byte oracle actually rerun. **182 original causal signal decisions, 0 synchronized tradable pairs, 0 certified complete lifecycles.** This proves only correct fixture checks and a source veto, **not** a profitable or executable historical engine.

Read-only diff audit from prior head `4df9bfc` through workflow `b5565e7`: prereg markdown, independent oracle, its test file and isolated CI workflow only; no frozen models, paper/results, legacy champion or sealed windows changed.

## Critical path still blocked
Required original 2021-12-09..2023-09-30 BTC+ETH Deribit options BBO+sizes, venue+arrival timestamps through full 21–45d entry/exit/settlement lifecycles, original dated fee tier, lot/margin/maintenance/liquidation and delivery index/fill receipts remain absent. Last authenticated vendor probe lacked `TARDIS_API_KEY`; ordinary 2026 subscription does not establish 2021 entitlement. A legally entitled Tardis Business/historical grant or independently verified equivalent Amberdata/CoinAPI archive with the same fields is necessary. Do not unlock validation [2023-10-01,2024-01-18) or holdout >=2024-01-18 without a new frozen TRAIN-passing integrated candidate.
