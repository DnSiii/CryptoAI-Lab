# V98 Independent — CZ/DA physical capital opportunity-cost diagnosis (2026-10-24)

**Scope:** artifact-only, no new trading PnL, no parameter search or revival. Independent read of pinned 2022-2024 USD10k native historical execution receipts for two **permanently rejected** seven-slot candidates. Audit run: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40156466818 . CZ original: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40156106166 . DA original: https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40156312719 .

## Verified complete versus core-only historical CAGR
| Candidate | Cost | Core-only CAGR | Complete CAGR | Difference in CAGR percentage points | Annual full-minus-core net log growth 2023 / 2024 |
| --- | --- | ---: | ---: | ---: | --- |
| CZ | Base | +104.45% | +84.01% | −20.44 pp | −0.15761 / −0.05320 |
| CZ | Severe | +96.64% | +71.63% | −25.01 pp | −0.19342 / −0.07887 |
| DA | Base | +62.47% | +21.41% | −41.07 pp | −0.35668 / −0.22646 |
| DA | Severe | +54.81% | +14.37% | −40.44 pp | −0.37018 / −0.23568 |

The complete portfolios lost annual net log growth against their own core-only ablations **in both years and both cost scenarios**. These are historical training-only numbers, not out-of-sample, not proof that a core-only engine is deployable, and not an invitation to resurrect rejected CZ/DA.

## Physical mechanism evidence
- CZ base: core-only peak gross/NAV **0.82094** versus complete **0.78316**, while turnover rose from **$444,235** to **$650,230** per USD10k start. Native funding improved (less paid) from **−$3,179** to **−$2,613**, but total net log wealth still deteriorated. Severe case: core-only gross/NAV 0.81692 versus complete 0.77852; turnover $418,945 versus $591,598.
- DA base: core-only peak gross/NAV **0.78717** versus complete **0.77686**; turnover roughly unchanged ($386,565 versus $384,660), yet complete wealth materially worse. Severe: gross/NAV 0.78226 versus 0.77172.
- Both complete engines recorded **100% maximum single-asset gross concentration** at some hour; source diversification does not imply realized physical diversification. These measurements support a *possible* shared-collateral displacement / sleeve-interference mechanism, but do not independently prove that the governor alone caused the loss.

## Critical-path decision
**No approved V98.** The next ex-ante complete architecture must explicitly address marginal *physically authorized* portfolio contribution and displacement, not merely source activity or gross standalone signals. A plausible distinct direction is an allocator with a causal, separately validated counterfactual physical marginal estimate and an enforceable opportunity-cost budget; prior CY shadow allocator failed, so its parameters/signals must not be reused. Require independent event-level replay and capacity/supersevere tests only after a new composed candidate passes training gates. Do not open 2025 holdout, 2026+ data, V14/V15/V99 or paper. No real trading authorized.
