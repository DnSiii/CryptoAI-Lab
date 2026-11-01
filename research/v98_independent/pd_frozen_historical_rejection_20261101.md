# V98 PD — irrevocable seven-slot training rejection (2026-11-01)

**Decision: REJECT_PD_TRAINING.** No post-result sign, threshold, cost, window, gross, allocator or sleeve rescue. PD is not a V98 champion, validated engine, paper PnL or live authorization.

- Immutable pre-result contract: [PD preregistration](pd_risk_premium_composition_prereg_20261101.md), commit `2952562045d29911aa3d5d298c2322243718cf27`.
- Source-gated physical run: [GitHub Actions 41270721141](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41270721141), commit `4a2a2fdd11e4f3022330513c2ef3d8989a68be20`. The run intentionally exits nonzero on economic rejection; **30/30 physical cells completed and passed execution feasibility**, not strategy economics.
- Unmodified full `PD_RESULT_JSON` copied from the job log and frozen as [PD training receipt](pd_full_training_frozen_result_20261101.json); 157 weekly decisions, 5 books, 3 cost tiers, 2 funding settlement orders.
- Independent signal/allocator oracle: 0 mismatches, maximum weight error 1.72e-14. 26,303 hourly cash identities and 210 net fill events independently reconciled, 0 discrepancies. [Independent frozen receipt replay 41270819395](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41270819395) **passed**, 60/60 arithmetic checks and **all 30 economic gate failures reproduced**. An independent JS-language arithmetic/gate replay additionally agreed 60/60 and 30/30.
- Training universe: BTCUSDT/ETHUSDT/BNBUSDT/SOLUSDT, 27,048 1h bars Dec-2022–Dec-2025 including warmup, 13,524 native funding *rate* events, 2025 already exposed for training. The funding mark is the signed conservative hourly mark envelope, **not exact event markPrice**.

| Full PD, carried-before-fill | Base | Severe | Supersevere |
|---|---:|---:|---:|
| Historical simulated CAGR | +3.92% | -0.44% | -4.92% |
| Maximum drawdown | -38.77% | -42.99% | -47.19% |
| Turnover USD, initial NAV USD10k | 1,134,296 | 1,062,521 | 991,747 |
| 2025 annual return | -18.24% | -21.72% | -25.30% |

**Marginal analysis (full minus corresponding sleeve ablation, log growth):** Opportunity +0.1051 base / +0.0893 severe / +0.0724 supersevere; RV -0.1149 / -0.1288 / -0.1446; Stress -0.0103 / -0.0125 / -0.0148. The Opportunity sleeve has **positive full-history marginal contribution** but fails the precommitted 2025 annual marginal floor: -0.0533 base, -0.0572 severe, -0.0615 supersevere. This is not sufficient to freeze a robust module or revive PD. RV and Stress actively reduce full-system growth. Economic failure includes insufficient CAGR, base/severe turnover >USD1m, negative 2025 return, and weak/negative optional sleeve contributions. Severe DD itself passes the -45% gate but does not rescue other failures.

**Next distinct work:** investigate an independently sourced return mechanism rather than reweighting PD, changing failed PD sleeve rules, or repeating price-only trend recipes. New work must be preregistered before seeing its results and must run full composed 7-slot ablations and physical gates. In parallel, obtain 13,524 original official `symbol,fundingTime,fundingRate,markPrice` records (3,381 per asset) with raw exchange-origin response/export, UTC chronology, original headers, SHA256 and independent rate/time reconciliation; official direct API from tested runner returned HTTP451. Authorized export from an accessible jurisdiction/network is the alternative. Without these marks exact funding settlement cannot be attested; conservative research may continue but not claim exact native PnL.

No 2026+, XRP, contaminated Phase083, V14/V15/V99 tuning/benchmark, V16/V99 Frozen, V99 paper, or live execution was accessed or modified. No engine approved.
