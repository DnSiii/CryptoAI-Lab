# V99 R106 S3 — independent original-source basis opportunity VETO (2026-10-30 00:47 BRT)

**NO ECONOMIC TRIAL / NO PNL / NO PROMOTION / NO THRESHOLD RETUNE.** The proposed distinct cash-and-carry (spot long/perpetual short) mechanism did not meet its *preregistered source/opportunity feasibility* requirements. This is **not** a trading-model rejection based on profitability, because no S3 strategy was executed.

## Evidence and chronology
- Ex-ante [S3 preregistration](V99_R106_S3_BASIS_CARRY_SOURCE_FEASIBILITY_PREREG_20261030.md) committed as `f7735d68c239c908a4e6cdc960d4e01de63f06a8` **before** any implementation and result. CI confirmed prereg ancestor.
- [GitHub Actions 40999189733 — SUCCESS](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40999189733); original first-party OKX BTC/ETH spot and swap TRAIN receipt archive from Actions `40019588739`; source-only artifact `12952711848`, digest `sha256:a43abb4d9c0f09a3685fa4c3d38f840ced8c0ace69b777f8e76610ebd9d6f97c`.
- Source feasibility [runner](../research/tools/v99_r106_s3_basis_source_feasibility.py) and separately coded [independent original-receipt/daily-decision oracle](../research/verification/independent_v99_r106_s3_basis_feasibility.py) both passed, with original four-leg source verification and no future or sealed price reads.
- Scope: 15,864 original hourly observations per leg, 631 fixed UTC 00:00 TRAIN decision days after 720h warmup, 5 chronological folds. Strict t-1 premium only.

## Numeric result (indicative opens, not executable spreads)

| Fixed preregistered criterion | Observed original TRAIN |
|---|---:|
| Positive swap-over-spot premium >= **2.90%** (supersevere 2.40% round-trip modeled two-leg friction + 0.50% buffer) | **0/631** unique decision days |
| BTC qualifying daily observations | **0** |
| ETH qualifying daily observations | **0** |
| Folds with >=1 eligible day | **0/5** |
| Eligible days by chronological fold | **[0, 0, 0, 0, 0]** |
| Maximum observed BTC indicative positive premium at daily decision | **0.049301%** |
| Maximum observed ETH indicative positive premium at daily decision | **0.145104%** |
| Independent original-source/eligibility oracle | **PASS** |
| Economic backtest, native funding/fees/fills | **NOT RUN / NOT AUTHENTICATED** |

The maximum indicative premium on either instrument was less than even the preregistered **severe** 1.00% two-leg round-trip modeled friction (4 x 25bps), *before* funding, margin, execution spread and adverse selection. This observation is a source feasibility failure for this **specific price-premium convergence design**; it does not disprove all carry strategies, and funding yield was not evaluated. No ex-post threshold reduction, alternative clock, or selective sample is permitted.

## Decision and critical path
**S3 ORIGINAL-BASIS OPPORTUNITY VETO — NO ECONOMIC ENGINE BUILT, NO RETUNE, NO PROMOTION.** Do not waste a new economic GitHub Actions cycle on this mechanism. C1, S1 and S2 remain permanently rejected, without rehabilitation.

The I1 derivatives architecture remains **SOURCE HOLD**: an authorized original Deribit 2022-01-23 sample with written redistribution/use entitlement, authenticated original hash, historical executable quotes/depth, fee-tier provenance and settlement/lifecycle records is missing; 658/661 historical days absent, 0/180 certified lifecycles. Alternatively, a genuinely different mechanism must first have complete original data and an ex-ante non-PnL opportunity/cost feasibility check. A data-only success cannot authorize economic deployment. For any spot/perp funding-based design, original 8-hour funding coverage, account-specific fee tier and contemporaneous executable depth/margin/liquidation rules are also mandatory; gaps cannot be filled with invented zero funding or hypothetical certified fills.

Frozen V16/V99, champion, paper/results, sealed validation [2023-10-01,2024-01-18), final holdout >=2024-01-18, and order interfaces were not touched. No ROI, realized paper, or live execution is claimed.
