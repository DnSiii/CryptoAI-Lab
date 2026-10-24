# V99 I1 — independently verified original TRAIN overlapping native-coin risk (2026-10-24 20:45 BRT)

**Decision: portfolio-level synthetic collateral assumption contradicted by original underlying paths; DATA_ONLY/HOLD — NO PROMOTION.** This is not an options backtest, a realized loss, historical liquidation, native exchange margin certification, or an approved trading engine.

## Execution and independent verification

- Precommitted before calculation at `bd84ef6293dadccb43b460c7f4e3bfdeffc7321e`: `research/V99_R106_I1_OVERLAPPING_COIN_EXPOSURE_PREREG_20261024.md`.
- Used the **unchanged original 661-day BTC/ETH first-party Deribit delivery-index TRAIN artifact** from successful Actions 40117855925. No validation [2023-10-01,2024-01-18) or final holdout >=2024-01-18.
- Implemented an illustrative 91-week per-asset 21-day overlapping 95%/90% put-vertical **intrinsic-only** obligation calculator with fixed 0.05-coin earmark per position, daily 08:00 original index, and up to four simultaneous positions at Monday expiry/entry snapshots. No premiums, fills, fees, funding, actual listed strikes, native maintenance margin, liquidations or ROI.
- [GitHub Actions 40143945726](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40143945726), job **121021244458**, **SUCCESS**. Primary calculator and independently written piecewise-payoff replay agreed on **1,304 daily asset-snapshots (652 per asset)**, complete source SHA and summaries. Mutating original source bytes or fabricated portfolio results was rejected. Artifact **12579987574**.
- Branch compare `e7ece86030c22220006e52b2ad30d2787444f706...d255757a8417e64d08cf79f0b481b766890a1b2d` confirms only four new research/workflow files; no immutable Frozen, paper/results, champion, dashboard or sealed partitions changed.

## Original underlying paths, synthetic strikes and coin earmarks — NOT options trading PnL

| Diagnostic | BTC | ETH |
|---|---:|---:|
| Daily index snapshots | 652 | 652 |
| Maximum simultaneous illustrative positions | 4 | 4 |
| Daily snapshots aggregate intrinsic obligation > aggregate earmark | **31/652** | **39/652** |
| Distinct synthetic spreads whose daily intrinsic coin obligation ever exceeded own earmark | **37/91** | **42/91** |
| Peak aggregate intrinsic coin obligation | **0.2348597113** | **0.2712523528** |
| Peak aggregate intrinsic / earmarked coin ratio | **1.5657314087×** | **1.7489095339×** |
| Independent cross-check: terminal-only single-position breaches | **25/91** | **27/91** |
| Max aggregate ratio in chronological snapshot folds 1–5 | 1.2426, 1.5657, 1.2213, 1.1711, 1.1298 | 1.3760, 1.7489, 1.2504, 1.1498, 1.0751 |

**Interpretation and limitation:** Under the explicitly hypothetical spread and coin-earmark construction, original BTC/ETH daily underlying paths expose additional within-holding risk and concurrent collateral demands missed by an expiry-only per-position view. This is an intrinsic-only *scenario proxy*: it is **not** a European option market mark, margin requirement or guaranteed lower bound on liquidation exposure; daily 08:00 snapshots also miss intraday extremes. Peak ratios must not be labeled account leverage, actual realized losses or exchange-certified liquidation risk. The I1 gross implied-minus-realized-variance structural screen is not a tradable return, and this diagnostic cannot rescue or reject a complete strategy.

## Actual critical path

**0/182 original eligible BTC/ETH asset-weeks with sufficient point-in-time executable option books** from the currently available two-day Tardis partial sample. No authenticated complete 2021–2023 historical Deribit BTC/ETH bid/ask **with sizes and exchange/local-arrival timestamps**, full holding-period liquidity/gap manifest, historical contract multiplier, coin collateral/margin/forced liquidation and account fee tier is available. A licensed Tardis archive with verified entitlement, or an equivalent demonstrably covered vendor archive, is required; the previously checked `TARDIS_API_KEY` was not configured. A vendor coverage proof and lawful data access must precede any purchase or economic claim.

**Next real step:** once licensed original complete entry and holding-period quote data and native terms are available, run **one** fully preregistered integrated, self-financing I1 engine on five fixed chronological TRAIN folds with severe/supersevere execution/funding/margin/tail/DD and benchmark gates plus independent trade/account replay. Do not open validation or final holdout without full TRAIN pass and formal freeze. In parallel, research one distinct integrated architecture supported by already complete native TRAIN data rather than serial synthetic option parameter tests.

**NO PROMOTION.** No live orders, no economic ROI, no paper-results changes.
