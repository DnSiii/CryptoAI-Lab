# V99 I1 — intraday chronological fold boundary correction: verified result (2026-10-29 BRT)

**Decision: SOURCE_ONLY/HOLD — NO PROMOTION. No economic TRAIN and no certified original option lifecycles.**

## Real defect and repair

The preregistered R106 folds switch at 2022-04-20 **04:00**, 2022-08-30 **09:00**, 2023-01-09 **14:00** and 2023-05-21 **19:00** UTC. The existing I1 numeric report has only 661 daily **23:59:59** NAV snapshots. Previously the code presented the full daily return on each boundary date as belonging to the new fold; this misassigns the pre-edge parts of the four days (4+9+14+19 = **46 intraday hours**) when claiming an exact five-fold result. The independent daily oracle reproduced that proxy, not the true intraday NAV.

Preregistered the correction before code in commit `445c159feb1d00870c5714c0cc80887af5c582c3`. The production numeric report now explicitly records `fold_attribution=DAILY_PROXY_NOT_EXACT`, lists the four missing original intraday fold boundaries, and **sets `exact_chronological_fold_gate_evaluable=false` and `exact_chronological_fold_gate_pass=false`**. The existing 661-day daily-proxy metrics are retained for reproducibility, but **cannot authorize formal five-fold TRAIN success or freeze**. No thresholds, strategy rules, historical outcomes or partitions were changed. The independent oracle separately checks the literal boundaries and rejects a forged exact-fold pass.

## Actual remote verification

- [GitHub Actions 40820182396](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40820182396) **SUCCESS** on commit `a75eef9bcafdb1f215ed6ebb6a2039ea4eaedbe8`; **11/11 tests pass**, including forged exact-fold claims, daily-only boundary list, independent replay and nonpromotion.
- Initial push CI [40820032271](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40820032271) **FAILED** for a pre-existing test fixture incompatibility: three old `fixture=False` tests still supplied one global `decisions` ledger after the real nonfixture engine was hardened to require two separate scenario-specific 180-row ledgers. Repaired **only those three stale test fixtures**, not the trading engine; successful CI confirms the fix. Earlier intermediate CI failures are not economic outcomes.
- Final CI explicitly printed `BLOCKED_ORIGINAL_ECONOMIC_SOURCE_PROVENANCE_NOT_CERTIFIED` and `0/180 original economic lifecycles certified`. All checks are synthetic/software controls, not original option PnL.

## Remaining critical path, without invented delivery

The daily numeric report **cannot** prove the exact original five chronological folds until the economic ledger can reconstruct original native USD-equivalent NAV at the four interior fold-edge hours, with independently replayed BTC/ETH coin balances, same-clock original index and held-option marks. The more fundamental external blocker is still the lawful **full 661-day 2021-12-09..2023-09-30 BTC+ETH Deribit original option BBO/sizes/arrival and lifecycle/delivery tape** (658 days absent beyond 3 sample days), plus dated historical fee tier, inverse-coin margin/liquidation, settlement and conservative size-aware simulated execution terms. Actual account fills cannot exist for unplaced hypothetical trades; modeled fills must remain labeled hypothetical.

Alternative: acquire **one previously selected, calendar-eligible, positive original TRAIN Monday's preceding-Sunday quotes** as a narrow source-feasibility test before committing to the entire archive; it does **not** replace 661-day economics. No serial candidate grids or posthoc I1 tenor changes.

**NO PROMOTION / NO ROI / NO ORDERS.** V16/V99 Frozen, legacy champion, paper/results, sealed validation [2023-10-01,2024-01-18) and final holdout >=2024-01-18 untouched.
