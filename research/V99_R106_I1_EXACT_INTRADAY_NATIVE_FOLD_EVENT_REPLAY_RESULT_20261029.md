# V99 I1 — exact native-event intraday fold accounting (2026-10-29 02:53 BRT)

**Decision: SOURCE_ONLY/HOLD — NO PROMOTION. No original economic TRAIN, no certified original option lifecycle, no validated trading engine.**

## Specific blocker reduced, without changing the strategy

The prior 661-day end-of-day native equity report attributed all returns on four boundary dates to the next chronological fold, despite the original immutable R106 TRAIN folds changing at 2022-04-20 04:00, 2022-08-30 09:00, 2023-01-09 14:00 and 2023-05-21 19:00 UTC. A daily proxy is not an exact five-fold result.

Preregistered the native event-derived solution **before code** in [commit 015c4924](https://github.com/DnSiii/CryptoAI-Lab/commit/015c4924ad728b5d0edcfe46c123e5405c03d6a7). The native 661-day BTC/ETH self-financing event replay now optionally captures all four exact-clock fold NAVs from the **same chronological OPEN/MARK/SETTLE_BATCH wallet**. It accepts only BTC/ETH same-clock source indices, not caller-supplied NAV. An open position must have all same-clock two-sided mark receipts at the boundary; flat wallets use their same-clock index. Rejects stale/missing marks, forged NAV, non-boundary inputs and severe/supersevere original-index substitution.

The numeric gate splits each boundary day's compounded factor into **old-fold pre-edge** and **new-fold post-edge** components; independent reference code recomputes the factors. With missing boundary source, the gate explicitly remains `DAILY_PROXY_NOT_EXACT` and exact-fold success is blocked. Even with all four synthetic snapshots, formal numeric pass, original economic certification, freeze and promotion remain **false**. Original daily metrics and fixed strategy rules are unchanged.

## Executed GitHub evidence

- [Actions 40825635909](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40825635909): prior native replay regression **SUCCESS** after source implementation.
- [Actions 40825661304](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40825661304) and [40825683825](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40825683825): numeric gate + independent oracle **SUCCESS** after respective changes.
- [Actions 40825728031](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40825728031): integrated exact-fold replay **SUCCESS, 38 synthetic/software tests**.
- [Actions 40825818674](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40825818674): **SUCCESS, 39 synthetic/software tests** after adding an actual open-position fixture crossing the 2022-04-20 04:00 edge. Same-clock original-style mark accepted; missing edge mark rejected. CI printed `EXACT_FOLD_ACCOUNTING_SYNTHETIC_ONLY; 0/180 ORIGINAL ECONOMIC LIFECYCLES; NO PROMOTION`. Independent numeric recomposition and tampering controls passed.
- Commit [7ae9b4c](https://github.com/DnSiii/CryptoAI-Lab/commit/7ae9b4c761c4170e83d471e1425bd32f7511bd06) contains the last test. Compared to prereg commit, only the native event replay, numeric gate, independent numeric oracle, synthetic test and dedicated CI workflow changed. No Frozen/paper/champion/holdout paths modified.

**These tests do NOT use original paid option quotes, historical original account fees, or real fills.** The four exact NAVs are demonstrated on synthetic wallet fixtures only; the original source remains missing. There is no claim of improved ROI, winning strategy, valid original five-fold TRAIN or economic superiority.

## Remaining actual delivery blockers

1. A lawful full original Deribit BTC+ETH option BBO/size/venue+arrival and same-contract mark/delivery archive covering **2021-12-09..2023-09-30**, including four intraday fold-edge marks and indices; **658/661 original days still unavailable** beyond the three public samples. The account has no verified paid historical Tardis entitlement/key or equivalent vendor grant. **Alternative:** first verify one *previously preselected, calendar-eligible, signal-positive* original TRAIN entry date under a written licensed grant; this only tests feasibility, not economics.
2. Dated 2021–2023 native contract multiplier/lot, account fee tier, delivery TWAP and margin/liquidation rules. Present-day Deribit documentation cannot certify historical terms. Model hypothetical size-aware fills conservatively; actual account fills cannot be invented for an untraded backtest.
3. A genuinely distinct, preregistered and scientifically rational complete engine with **full original TRAIN economics** and independent oracle, 5 exact chronological folds, six regimes, severe/supersevere, DD/tails/benchmarks. Previously rejected C1/D1/E1/F1/G1/H1 must not be retuned; I1 remains de-prioritized and source-blocked. No new candidate was tested in this cycle.

**NO PROMOTION / NO ORDERS / NO HISTORICAL ROI.** Validation [2023-10-01,2024-01-18), final holdout >=2024-01-18, V16/V99 Frozen, paper/results and legacy champion untouched. This is an hourly scheduled execution, not continuous live operation.
