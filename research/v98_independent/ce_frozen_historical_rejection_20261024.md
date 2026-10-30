# V98 Independent CE — frozen original persistent market-premium seven-slot historical rejection (2026-10-24)

**FINAL DECISION: REJECT_CE_HISTORICAL_GROWTH_OR_MARGINAL.** CE is not approved, not 2025 validated, not deployable, not future PnL and not authorized for paper/live trading. All original CE signals, windows, thresholds, budgets, execution logic and ablation gates are frozen; no post-result rescue.

## Immutable chronological evidence

- Preregistered independent persistent market-premium hypothesis **before economics** at commit `496a3ec03e8768bfa410077f784b11c0dd9da673`. Original source committed `f0e618622fd7d3b2b25e50360dadf722ffd5ba21`.
- Official [CE 90-cell two-OS training + independent replay](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40113695254), original workflow commit `d37fabc5228e42e8bb800e4e56a7c73ded09d4c5`. **90/90 physically survived, two Ubuntu environments reconciled, zero receipt errors.** Native signed funding, actual-open settlement and independent 81-corner arithmetic replay passed six USD10k full-book cases. Mechanical passes are NOT economic validation or real exchange fills.
- Authenticated Clean-4 BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT Binance USD-M 1h Dec2022–Dec2024 only, signed native 8h funding. 2025 holdout sealed; 2026+ excluded; XRP quarantined; Phase083 invalid; V14/V15/V99 and paper untouched.
- The replay artifact inside the original workflow was **misnamed** `cd-independent-event-replay` by the workflow's artifact label, although the executing source was `ce_event_replay_audit.py` and logs/receipt identify `CE`. This label is a traceability caveat, not a claim that CD was rerun.

## Original complete CE USD10k, carried-before-fill — historical training ONLY

| Cost | 2023 net | 2024 net | Two-year CAGR | Max DD | Signed funding | Fees + slippage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Base | **−1.5218%** | **−0.2920%** | **−0.9082%** | 20.7590% | −USD139.28 | USD960.79 |
| Severe | **−17.4859%** | **−9.4344%** | **−13.5452%** | 36.7008% | −USD114.51 | USD4,027.44 |

Both annual growth gates fail under both funding orders; both CAGR floors (>50% base, >30% severe) fail. Severe DD passes its <45% ceiling but does not rescue negative growth. Full portfolio 95 physical fill hours, 48 authorization updates, **47 forced risk ratchets** under both base and severe: near one forced reduction per update, indicating inadequate persistent exposure and repeated cost-bearing reauthorization. This is an economic/physical bottleneck, not merely a missing alpha signal. No assertion that all 47 ratchets were immediately executable exits; the physical governor's staged settlement still controls fills.

## Original USD10k full-minus-ablation annual net log-growth marginal

| Module | 2023 base | 2024 base | 2023 severe | 2024 severe | Original gate |
| --- | ---: | ---: | ---: | ---: | --- |
| Opportunity | +0.000291 | +0.007543 | +0.002278 | +0.201243 | **PASS within rejected CE only** |
| Relative Value | −0.012574 | −0.127871 | −0.011788 | +0.129172 | **FAIL** |
| Stress/Recovery | −0.015628 | −0.244017 | −0.058977 | −0.242746 | **FAIL** |

Opportunity's original portfolio-level marginal was positive in both years/base/severe and both funding orderings, but **CE as a complete engine is permanently rejected**. No transplant, retuning or cosmetic rescue is authorized. Core-only original severe CAGR **−6.743%**, with 8 authorization updates, **8 forced ratchets** and only 16 physical fill hours. A structural failure of inventory persistence/physical authorization is evident even without satellites; repeatedly searching more signals without resolving that bottleneck is unlikely to deliver a strong compounded engine.

## Decision and next critical path

**Do not repeat CE or loosen costs/risk to make the original pass.** A genuinely distinct, preregistered architecture must first verify a new **causal, conservative, physically staged inventory persistence and risk-reentry mechanism** under the same source and stress rules, without relying on free immediate exits or hidden leverage. Demonstrate that it can actually maintain economically meaningful exposure and reduce forced churn, then integrate four genuinely independent module economics, full seven-slot portfolio, severe/supersevere costs, independent event replay, and chronological validation. Historical tests and cashflow checks are not live trading proof.

All CE writes confined to `research/v98_independent/ce_*` and `.github/workflows/v98-independent-ce-*` on `research/v98-independent-zero`; V16/V99 Frozen, V99 branch/workflows/reports and paper unchanged.
