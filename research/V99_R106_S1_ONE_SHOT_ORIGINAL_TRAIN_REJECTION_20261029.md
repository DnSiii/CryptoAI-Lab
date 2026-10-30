# V99 R106 S1 — one-shot original-source complete TRAIN REJECTION (2026-10-29 21:56 BRT)

**FORMAL DECISION: S1 PERMANENTLY REJECTED / NO RETUNE / NO PROMOTION.** This is a real original-OKX-price, **modeled-cost** historical TRAIN replay, **not** exchange-executed orders, historical account profits, paper PnL, or certified fills. No validation, holdout, Frozen, champion or paper updates.

## Preregistration, implementation and CI
- Exact rules and gates committed **before performance** in [5fd5b0d](https://github.com/DnSiii/CryptoAI-Lab/commit/5fd5b0d7f8e731530a0f7c0a1b734a2d4b617981); final indexing/terminal-liquidation clarification also committed before performance in [34d58e5](https://github.com/DnSiii/CryptoAI-Lab/commit/34d58e596d6c846609179a9e11adbe6fb1e048b0). The workflow verified the preregistration commit is an ancestor.
- Complete spot-only BTC/ETH relative-overreaction system: fixed 72h divergence, prior 720-observation BTC trend veto, prior 72h volatility veto, 65% laggard spot/35% cash, daily UTC causal decisions, self-financing cash/units, terminal liquidation. **Not** rejected C1/C2 trend, D1 carry or I1 options.
- First-party original OKX four-leg 2021-12-09 to 2023-10-01 exclusive price artifact from [Actions 40019588739](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40019588739) independently reverified; **15,864 original hourly TRAIN observations per leg**; no funding required for spot-only S1. All price opens are source evidence, **not** executable fill quotes.
- [Actions 40982466317](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40982466317) failed on shallow Git checkout in the prereg ancestry check, **before** market data/performance. [Actions 40982500657](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40982500657) executed modeled TRAIN but its independent checker failed on a report key-name mismatch (not a PnL disagreement). Both defects were repaired without changing frozen economic parameters or reranking outcomes.
- [**Actions 40982638347 — SUCCESS**](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40982638347), commit **e7ce9ac60e21572b753ceae8a63d27994e663c3c**. The independent oracle separately reparsed original market receipts, independently recomputed the exact causal signals, per-hour spot units, cash, turnover, fee, NAV, five chronological folds, 3x2 regime attribution, maximum drawdown, best-day removal and two scenario traces for all **15,864 hours**. Both scenario NAV digests, decision digests and account statistics agreed. Result artifact **12944829659**.

## Frozen one-shot results (modeled, NOT exchange-certified)

| Metric | Severe (25 bps one-way modeled) | Supersevere (60 bps one-way modeled) |
| --- | ---: | ---: |
| TRAIN ROI | **-17.6307%** | **-20.9293%** |
| Max drawdown | **-19.5788%** | **-22.6241%** |
| Positive chronological folds | **1/5** | **1/5** |
| Worst fold | **-10.9610%** | **-12.9640%** |
| Fold ROI 1 | +1.1859% | +0.7247% |
| Fold ROI 2 | -10.9610% | -12.9640% |
| Fold ROI 3 | -7.9345% | -8.7597% |
| Fold ROI 4 | -0.6956% | -1.1460% |
| Fold ROI 5 | 0.0000% | 0.0000% |
| Nonzero turnover events | 22 | 22 |
| Modeled fees/slippage paid, initial NAV=1 | 0.026416 | 0.062164 |
| ROI without best day | -21.6208% | -24.7551% |

Original source-based investable passive **severe** benchmarks over active period, entry+terminal cost modeled: BTC **-35.3318%**, ETH **-47.8802%**, 50/50 **-41.6060%**, cash **0%**. S1 lost less than BTC/ETH but did not beat the cash benchmark, and that relative performance does **not** justify promotion.

**Gates:** positive both FAIL; 4/5 folds FAIL; worst fold >=-5% FAIL; DD >=-25% PASS; severe beats full passive envelope FAIL; 4/6 positive regimes FAIL; best day removed positive FAIL; source and accounting PASS; authenticated native fee/fill provenance FAIL. This is **not** an economic winner. 1/5 positive folds cannot be rescued by a parameter tweak or by relabeling modeled fees as native.

## Scientific and operational boundaries
- **S1 is permanently rejected, no retuning, no further S1 parameter variants or sealed validation.** The historical price feed and modeled accounting are reproducible; native historical account-specific fee tier, actual historical fills and orderbook liquidity are **not** authenticated. Historical hypothetical orders cannot acquire retrospective real fills.
- The exact severe/supersevere causal decision SHA is identical: `f92801d0f9a0ead8b8ec5d32400b1d80c8caa22b057b1db62be6763f42e23612`. Per-scenario NAV trace hashes: severe `fac32d6dbbc4814799264efec515b21d38ee4fcdb56c2428dda3c88e5bece1ab`; supersevere `97b178f6667b9eb39ff81458c75cd64a9cfeadc75af07ca8ff3712fa6ac59694`.
- Read-only [commit comparison](https://github.com/DnSiii/CryptoAI-Lab/compare/debedb44afc0bd8fcdd5fa1812baa06b9bc61338...e7ce9ac60e21572b753ceae8a63d27994e663c3c) confirmed **exactly four new paths**, no modified/deleted existing files: S1 prereg, runner, independent oracle and workflow. Frozen V16/V99, paper/results, legacy champion, sealed validation [2023-10-01,2024-01-18) and final holdout >=2024-01-18 remain untouched. No real orders.
- I1 remains **SOURCE HOLD**: licensed 2022-01-23 Deribit options sample and independent vendor digest, license, gaps, full original 661-day source, native execution/cost evidence remain missing; **658/661 days absent, 0/180 certified lifecycles**. Cross-venue funding December 2021 remains missing. D1 frozen basis carry is separately **REJECTED** by original-source funding upper-bound impossibility; do not resume D1 integration.

**Next critical step:** do not chase S1 returns. Prioritize a source-feasible, ex-ante economically motivated **distinct** integrated architecture only after explicit failure-mechanism analysis; in parallel request the I1 one-day authorized original source (no blind 658-day purchase). Neither synthetic CI success nor this original-price modeled TRAIN result permits unlocking validation, final holdout, Frozen, paper, champion or live trading.
