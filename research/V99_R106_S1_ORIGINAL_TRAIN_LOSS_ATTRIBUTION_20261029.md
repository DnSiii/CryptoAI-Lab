# V99 R106 S1 — original TRAIN structural loss attribution (2026-10-29 22:45 BRT)

**Decision: S1 PERMANENTLY REJECTED / NO RETUNE / NO PROMOTION.** This is a **read-only** forensic examination of the already-rejected one-shot S1. It is not a new candidate, optimization, native-fill profit statement, or permission to open validation/holdout.

## Source, independent replay and exact run

- [GitHub Actions 40987601224 — SUCCESS](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40987601224), source script `research/verification/v99_r106_s1_loss_attribution.py`, read-only forensic artifact **12947173348**, digest `sha256:7c6475d32a06c06309907770535159a263f5273776f03cedfda1d35e04af11a8`.
- Original OKX BTC/ETH spot TRAIN opens from previously archived [Actions 40019588739](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40019588739), **15,864 original hourly observations** per spot leg, ending strictly **before 2023-10-01**. Reused immutable published S1 rejected economic report from [Actions 40982638347](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40982638347), not a rerun with changed rules.
- Before attribution, the existing **independent original-source and per-hour accounting oracle** re-executed both severe and supersevere scenarios and passed; new forensic program then reconciled ROI, turnover, trade-event count, modeled fees, max drawdown and decision count against the original published rejection. Self-financing gross-minus-cost and per-fold/per-asset additive decompositions passed. Fail-closed NO PROMOTION, NO VALIDATION, NO HOLDO​UT, NO PAPER and NO ORDERS checks passed.

## Exact failure mechanism (NAV starts at 1; gross/cost are additive dollars per initial 1 unit NAV)

| Same frozen S1 decision rules | Gross mark-to-market PnL | Modeled friction | Net PnL/ROI | Turnover events |
|---|---:|---:|---:|---:|
| Zero-friction **diagnostic only** | -0.151906 | 0 | **-15.1906%** | 22 |
| Severe 25bps one-way modeled | -0.149890 | 0.026416 | **-17.6307%** | 22 |
| Supersevere 60bps one-way modeled | -0.147128 | 0.062164 | **-20.9293%** | 22 |

- **The structural edge is negative before friction**: even zero modeled trading cost loses **15.19%**. Friction aggravates the loss, but does **not** explain the strategy's fundamental failure. Gross PnL differs across cost paths because positions/capital scale after each modeled fee; it must not be treated as a signal improvement.
- **631 daily TRAIN decisions** after 720h warmup: only **17** crossed the preregistered absolute 72h BTC–ETH divergence threshold, **4** of these were vetoed, leaving **13** positive exposure decisions and **618** cash decisions. The BTC trend veto was true on 49 decision days, the volatility veto on 16 (these can overlap and must not be added). 22 actual turnover events across both cost scenarios.
- Severe fold **gross dollar PnL** (not independent fold ROI): **+0.015142, -0.095959, -0.065987, -0.003086, 0.000000**. The second and third chronological folds explain most of the negative gross PnL. This is descriptive attribution, **not** authorization to remove those folds or optimize a calendar filter.
- Additive reconciliation: severe **-0.149890 - 0.026416 = -0.176307**; supersevere **-0.147128 - 0.062164 = -0.209293** (rounding). Both match previously rejected published ROI.

## Consequence for critical path

**Do not retune S1, retry its thresholds, reuse it as a winner, or claim that cheaper execution rescues it.** Source and modeled ledger are adequate to reject this specific economic hypothesis. An alternative complete architecture must have a *distinct ex ante economic mechanism* and original-source feasibility before one-shot TRAIN. The derivatives I1 path remains separately **SOURCE HOLD**: the original licensed Deribit 2022-01-23 sample with written entitlement, original digest and full 661-day lifecycle coverage is not delivered; **658/661 days missing, 0/180 certified lifecycles**. Do not buy the entire archive before a single-day original-source feasibility check. Historical actual fills for hypothetical orders cannot be retroactively certified; native fee tiers, contemporaneous executable quotes/depth and settled funding (where applicable) require authentic evidence or explicit model-only limitation.

**No promotion.** Frozen V16/V99, paper/results, champion, sealed validation [2023-10-01,2024-01-18), final holdout >=2024-01-18 and live order interfaces remain untouched. The forensic CI success is not a validated profitable V99.
