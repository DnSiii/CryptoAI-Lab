# V98 PM — frozen full-history economic rejection (2026-11-01)

**Binding decision: REJECT_PM_TRAINING permanently.** Preregistered `pm_volatility_release_prereg_20261101.md` was committed as `04fe220c773b49682677b94496487276b6b3dd68` before PM implementation and before economic data were inspected. Physical + independent audit workflow: [run 41313237117](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41313237117). Frozen 30-cell receipt `pm_full_training_frozen_result_20261101.json`; frozen independent receipt audit `pm_frozen_independent_receipt_audit_20261101.json`. The workflow's final red status is intentional preregistered economic rejection, not a runtime, source or reconciliation failure.

## Actual exposed-training physical simulation (2022-12 warmup through 2025-12)

30/30 physical cells feasible, 157 weekly decisions, 26,303 hourly cash identities, 13,524 native funding events priced at conservative **hourly mark envelope** (NOT exact exchange event mark), 108,192 authenticated premium-index asset-hours SHA256 `c301a38642f229ca2746ae33baaf58e4bb21ac280a1a99dbbc328cc074caaad4`. All premium signals use only closed t-1 bars; funding event t excluded at decision t. No 2026+, holdout or external benchmarks.

| PM full carried-before-fill, simulated | Base | Severe | Supersevere |
|---|---:|---:|---:|
| CAGR | +17.64% | +13.42% | +9.06% |
| Max drawdown | -27.73% | -29.10% | -30.55% |
| 2023 | +44.84% | +39.20% | +33.38% |
| 2024 | +15.91% | +11.49% | +6.94% |
| 2025 | **-3.01%** | **-5.97%** | **-9.06%** |
| Turnover from USD10k initial | USD1,154,447 | USD1,089,115 | USD1,024,129 |

Base full portfolio: 151 net fill events, 23 forced safety fills; fees USD461.78, slippage USD230.89, funding cash **-USD709.28**; 343/1,096 positive days; worst 1% daily mean **-4.88%**; hourly NAV-change Profit Factor **1.0221**, hourly payoff **0.9883**, hourly win rate **50.84%** (NOT trade-level PF/payoff/win). Peak single-asset gross concentration **100%**. The gross governor prevented leverage/insolvency but did not create net alpha.

## Independently verified binding rejection

Independent scalar oracle: **0** signal/allocation mismatches over all 157 decisions and five books, maximum numerical feature/weight error 7.44e-15. Raw optional activations: Opportunity **3**, Relative Value **31**, Stress/Recovery **4** weekly decisions. Independent cash reconciliation **0 mismatches** over 26,303 hours; independent fees/slippage/funding oracle **0 mismatches**, 151 fill events. Separate receipt audit: **60/60 arithmetic checks**, **22/22 binding economic failures independently reproduced**, **4/4 receipt tamper cases rejected**.

Base leave-one-out net log-growth marginals: Opportunity **+0.00843**, Relative Value **+0.01295**, Stress **-0.00834**. Severe: Opportunity **+0.00821**, Relative Value **+0.00205**, Stress **-0.00998**. All three fail preregistered +0.02 net marginal floor. The full engine also fails base CAGR >80%, severe CAGR >60%, base/severe USD1m turnover limit, and severe positive-2025 gate. Both funding orders reproduce these failures. No parameters, signs, windows, gross or costs may be adjusted to rescue PM.

## Critical path and next distinct research boundary

This rejection is evidence of **insufficient optional contribution and 2025 net weakness**, not a reason to reopen PM. A future preregistered hypothesis must derive independent return economics with adequate nonzero incidence and positive net contribution, rather than rely on rare volatility-squeeze triggers or a sparse crash sleeve. New source evidence is useful only if it changes causal economic feasibility, not as a cosmetic extra phase.

The **13,524 exact Binance USD-M funding-event `markPrice` objects** are still missing because historical API access returned HTTP 451. Needed: symbol, fundingTime, fundingRate, exact markPrice, original raw exchange response, original HTTPS URL, HTTP headers including Date, UTC retrieval time, SHA256 and authorized independently verified custody. Alternative: authorized exchange-origin raw export satisfying `v98_exact_funding_mark_authorized_handoff_20261101.md`; archived funding rates and premium candles are not exact settlement marks. Untouched prospective validation/final holdout also missing; no complete V98 champion, no V14/V15/V99 comparison, no paper/live authorization. V16 Frozen, V99 Frozen/research/workflows/reports/paper, Phase083 and 2026+ were neither accessed nor modified.

**Scope audit:** only `research/v98_independent/pm_*` and `.github/workflows/v98-independent-pm-volatility-release-full-training.yml` were created in this cycle.
