# V99 R106 D3 — original TRAIN relative-value complete engine: PERMANENT REJECT (2026-10-29 08:47 BRT)

**REJECT_D3_NUMERIC_TRAIN_PERMANENT_NO_RETUNE. NO PROMOTION / NO ORDERS / NO PAPER / NO VALIDATION / NO HOLDOUT.**

## Ex-ante registration and non-reuse
The single BTC/ETH *cross-asset* perpetual relative-value reversion mechanism was preregistered **before code or historical D3 PnL** at [commit 3e5ddd2](https://github.com/DnSiii/CryptoAI-Lab/commit/3e5ddd2ab56381fa0ba88917757c7373c0daf3a9). This is not a posthoc retune of rejected D2 within-asset spot/perp basis, C1 trend, E1 passive spot, D1 funding carry, I1 options, weekly relative-strength rotation, or Donchian breakout. No parameter grid was searched.

Frozen rules: lagged 720-hour log ETH/BTC perp ratio z-score; enter rich/cheap spread at |z|>=2, equal initial 0.20 USD notional each leg; exit at |z|<=0.25, 168h hold or TRAIN terminal; 168h cooldown. Strict t-1 signals and contemporaneous original hourly open marks. Two fixed modeled friction scenarios, same trade schedule. No native funding, account fee, margin or actual fill certification.

## Real original source and independent economic replay
[GitHub Actions 40867901801](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40867901801) **SUCCESS**: 5/5 synthetic adversarial software controls, archived original first-party OKX raw-page proof for four BTC/ETH spot/perp legs, complete strictly isolated **15,864-hour TRAIN** [2021-12-09,2023-10-01), one-shot D3 portfolio simulation, and a separately implemented **15,864-hour independent** original-price -> lagged-z -> entry/exit -> fee -> NAV -> fold/risk/tail/gate replay. The oracle matched **50 hypothetical OPEN/EXIT events = 25 completed spreads** and both NAV paths. These are *not* orders or exchange fills.

Reproducible full hourly journals, decision and oracle are archived as artifact **12893594328** (`v99-d3-original-train-independent-40867901801`, SHA256 `3b867939edfea8d7bc9385b6df0530e6477914548e2f74fff352c47da2036948`). The Actions job completed, but **economic gates failed**.

| Preregistered TRAIN metric | Severe modeled 0.0007 per side/leg | Supersevere modeled 0.0014 per side/leg |
|---|---:|---:|
| **Pre-funding hypothetical ROI** | **-4.770093%** | **-6.181385%** |
| Positive chronological folds | **1/5** | **1/5** |
| Maximum drawdown | -7.947795% | -8.617146% |
| Hourly profit factor | 0.954742 | 0.942039 |
| ROI removing best hour | -5.374110% | -6.779768% |
| Top 1% positive-hour gain concentration | 33.9226% | 33.9177% |
| Worst 1% negative-hour loss concentration | 33.5435% | 33.1508% |
| Fixed 50/50 spot benchmark ROI | -54.3686% | -54.3686% |
| Failed preregistered gates | **5/10** | **5/10** |

Failed in BOTH scenarios: positive total ROI, required positive folds, hourly profit factor >1, positive ROI after removing best hour, and beating BOTH cash and the spot benchmark. All six descriptive 3x2 regimes occurred; tail-share and drawdown gates passed, but those cannot compensate for a negative edge. The spot benchmark is deeply negative; losing less than spot is **not** evidence of positive after-cost alpha.

## Binding decision and next critical path
**D3 is permanently rejected on its first original-source economic TRAIN.** No changes to 720h z window, thresholds, cooldown, sizing, directions, friction, fold boundaries or selection after seeing returns. Do not resurrect D3 by labeling green CI as success. Funding, native account fees, historical hypothetical execution fills/slippage, margin/liquidation remain unauthenticated. Even before funding, D3 failed decisive growth gates; there is no rational basis to spend cycles certifying D3 for promotion.

This is the third distinct original-source architecture recently rejected (D2 and E1 also rejected); **stop serially inventing price-only variants to chase PnL**. Focus the next work on a source-backed, structurally identifiable positive-expectancy mechanism and its native economic feasibility *before* another complete-system preregistration. The blocked I1 options route still requires a dated written license/entitlement, one authorized nonsample Deribit BTC/ETH 24-hour original bid/ask/size/clock tape, then complete 661-day coverage and exchange instrument/fee/margin/delivery rules. Only 3 free sample days are known; **658 original days remain absent**, and **0/180 I1 lifecycles economically certified**. An independently authenticated equivalent vendor archive is an alternative. This missing licensed historical market evidence prevents I1 complete original economic TRAIN; a successful synthetic importer cannot replace it.

Frozen V16/V99, legacy champion, paper/results, sealed validation [2023-10-01,2024-01-18), and final holdout >=2024-01-18 were not accessed or modified. No live orders. **NO PROMOTION.**
