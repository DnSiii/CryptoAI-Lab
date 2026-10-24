# V99 R106 G1 — fixed-rule dated-futures TRAIN structural rejection (2026-10-23 BRT)

**FINAL G1 DECISION: PERMANENT TRAIN STRUCTURAL REJECTION — NO RETUNE — NO PROMOTION.**
This is a causal original-source **entry/fold feasibility rejection**, not a
completed futures economic backtest. No historical ROI, account PnL, exchange
fills or native contract cash settlement is claimed. No orders, paper writes,
V16/V99 Frozen changes, legacy champion changes, validation or holdout access.

## Direct evidence and independent verification

- G1 was preregistered in
  [G1 fixed rules](V99_R106_G1_DATED_FUTURES_PREREG_20261023.md)
  before this source screen. The unchanged rule requires Monday 00:00 UTC,
  earliest 30–110 day USDT-linear dated expiry, **prior completed 1H close**,
  annualized positive basis >10% and gross premium >0.73% (0.48% severe
  four-side round trip + 0.25% reserve). Supersevere entry-cost envelope
  requires >1.21% gross premium. No intra-week entries.
- [Original spot TRAIN source receipts, Actions 40019588739](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40019588739)
  were independently verified at original page/1H-grid level. The entry
  screen used original confirmed **close** (not the separate open-only series).
- [Corrected original G1 futures TRAIN source audit, Actions 40052913340](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40052913340)
  independently reexecuted 59,560,082 original OKX trades and SHA-256-bound
  derived bars. Its **36,414 required / 187 no-trade-or-uncovered hours**
  are a *portfolio-valuation source blocker*, not an assumption of zero price.
  [Daily repair, Actions 40052902887](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40052902887)
  recovered 48 original trade hours and confirmed no trades in the other 139.
- [G1 original fixed-rule entry CI 40055562332](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40055562332)
  **passed**: original receipts and derived SHA-256 checks, t-1 decision
  timestamps, five unchanged chronological folds, exact cost/annualization
  inequalities, and a separately implemented expiry-to-fold reachability
  oracle. Original source-derived event artifact:
  `v99-g1-original-train-entry-screen-40055562332`.

## Decisive original TRAIN signal distribution

There are **83 fixed Monday decisions per asset**. BTC has 83/83 known
t-1 source closes, ETH 82/83; the one ETH missing original future close is
**2022-01-24**, fold 1. Missing source is treated conservatively as a
**possible positive entry**, never silently as a rejected signal.

| Asset | Known qualifying severe entries | Known supersevere cost-envelope entries | Missing t-1 entry inputs | Qualifying folds |
| --- | ---: | ---: | ---: | --- |
| BTC | 1 | 1 | 0 | 1 only |
| ETH | 3 | 3 | 1 | 1 only |

All four known positive severe entries are on **2021-12-13 (ETH),
2021-12-20 (ETH), 2021-12-27 (BTC and ETH)**, all referencing
**BTC/ETH-USDT-220325**. Original positive gross premiums were approximately
**2.56% BTC** and **2.66–2.87% ETH**; the preregistered annualized premium
was above 10% in these four observations. The only unknown Monday
(2022-01-24 ETH) also references **ETH-USDT-220325**. The dated contracts
expire **2022-03-25 at 08:00 UTC**, strictly before the end of fold 1
(2022-04-20 04:00 UTC).

**Conservative independent reachability:** even counting the unknown as
a profitable entry and allowing every known qualifying entry to remain
open until contractual delivery, G1 has possible trading exposure in
**fold 1 only**; **folds 2–5 have zero possible G1 trading exposure**.
Consequently the preregistered severe **>=4/5 positive trading folds**
gate cannot be met by this fixed engine. Unknown native mark prices,
fees or liquidation rules cannot create a preregistered G1 trade in those
four folds. Unpreregistered positive interest on idle cash cannot be
credited as G1 trading alpha.

**Permanent rejection, without parameter change or historical return
calculation.** Do not reoptimize the 10% annualization threshold, Monday
frequency, 30–110-day selection, expiry universe, fee reserve, or
instruments based on these observed results. This is a scientifically
meaningful hard failure, not an engineering milestone or a simulated
ROI rejection.

## Honest unresolved provenance (does not rescue G1)

139 required original future-hours have no matching trades in verified
monthly/daily archives; original mark/index values and exact delivery
settlement fixes for these hours are not authenticated. Contract-specific
2022/2023 `ctVal`, lot/minimum, margin/liquidation, fee tier, delivery
and collateral/borrow terms remain unproven by historical native receipts.
Current OKX terms are not retroactive evidence; historical hypothetical
fills cannot be relabeled real account executions. These issues would
block certification **if** G1 had survived the structural gate. Do not
spend further cycles reconstructing G1 economics after this permanent
rejection.

## Next actual critical path

Stop G1. Investigate the next **economically distinct** mechanism
without an uncontrolled posthoc series of PnL trials. Before a new
candidate is run, require an ex-ante causal edge hypothesis, source
availability for its actual cashflows, a fixed cost/margin model,
five unchanged chronological TRAIN folds and 3x2 regimes, independent
original-price-to-cash accounting, severe/supersevere adverse shocks,
tail/DD and fixed benchmarks. Only a complete new candidate passing
TRAIN and formally frozen may open sealed validation
[2023-10-01, 2024-01-18); final holdout >=2024-01-18 remains sealed.

**NO PROMOTION. NO ORDERS. NO REALIZED PAPER. NO HISTORICAL ROI CLAIM.**
