# V98 Independent OZ — FROZEN ECONOMIC REJECTION (2026-10-31)

**Binding decision: REJECT_OZ_TRAINING; no validated complete V98 champion.** Do not alter OZ signs, windows, weights, gross, costs, breakout/hedge triggers, or any gate after seeing results. All values are hypothetical exposed-training simulations, not paper or live PnL.

## Immutable chain
- Preregistration: `oz_structural_trend_prereg_20261031.md` committed as `ced59a1b5d848657425bdb627517ab051b94583b`, cold-start guard committed `5b24ec3416db8ec4fd478e1c203762a49ada3778`, **before** OZ economic run.
- First complete physical execution: [GitHub Actions 41258490294](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41258490294), pinned source commit `b8f116bc53a339be73c96d37cf9d0e546f7c6f9e`. Deliberate exit 1 signals economic rejection after 30/30 completed cells, not a runtime crash. Original artifact ID `13063174304`.
- Original `OZ_RESULT_JSON` from first run frozen without strategy edits in `oz_full_training_frozen_result_20261031.json`, commit `0bc3845f72e25e7a8d60d556a80a39f141767f89`.
- Separate [independent frozen economic receipt audit 41258590999](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41258590999): **PASS_INDEPENDENT_OZ_RECEIPT_RECONCILIATION_NOT_ENGINE**, 30 cells, 60/60 arithmetic checks, all 18 binding failures rederived, maximum arithmetic error 0.

## Original complete-portfolio physical training economics
Initial hypothetical USD10,000; Binance USD-M native funding rates with conservative official hourly mark envelope, not authenticated exact event settlement marks. Carried-before-fill order:

| Cost tier | CAGR | Max drawdown | Turnover USD | Ending hypothetical USD | Annual 2023 / 2024 / 2025 |
|---|---:|---:|---:|---:|---|
| Base fee 4bps + slippage 2bps | **+36.2728%** | -33.0719% | 1,039,227 | 25,311.61 | +76.94% / +14.11% / +25.36% |
| Severe 10+10bps | **+32.4500%** | -34.4701% | 990,179 | 23,240.18 | +72.45% / +10.33% / +22.14% |
| Supersevere 15+20bps | **+28.4656%** | -35.9391% | 940,668 | 21,204.84 | +67.77% / +6.42% / +18.77% |

Base hourly NAV-increment PF 1.03167 (**not trade-level PF**), 495/1096 positive days. Max single-asset gross concentration 100% at some point, not a diversified survival guarantee.

## Binding economic decision
- **18 economic failures** across two funding orders: base/severe CAGR thresholds (>80%/>60%), base turnover >USD1m, and all three optional sleeve full-minus-ablation net log-growth thresholds >0.02.
- Base full-minus-Opportunity **-0.005013** log; full-minus-Relative Value **+0.015774** log (positive but **below** binding +0.02); full-minus-Stress **-0.012780** log. Severe: -0.006128, +0.014467, -0.013285. Thus optional sleeves do not earn their allocation and cannot be cosmetically rescued.
- Base core-only CAGR **+36.219%** vs complete **+36.273%**; severe core-only **+32.539%** vs complete **+32.450%**. The full engine is not a materially stronger composed portfolio despite positive core trend returns.
- Severe drawdown -34.47% and all three severe years positive, but this does not offset failed growth and sleeve gates.
- Causal 157 weekly decisions and four mandatory cold-start cash decisions; independent signal/allocator mismatches 0. Independent cash identity: **26,303 hours**, mismatches 0, max USD 3.64e-12. Independent fee/slippage/funding oracle: **159 net fill events, 3,287 funding hours**, mismatches 0. Mechanical reconciliation is **not** economic success.

## Next critical architectural decision
Do not create OZ threshold/sign/gross rescues or relabel its +36% CAGR as a champion. The failure is **system capital efficiency and negative optional sleeve contribution**, not unit tests or a missing physical run. The next materially distinct architectural research should address actual positive marginal sleeve economics and explicit survival-constrained growth rather than swap one weekly indicator for another. Keep previously rejected candidates frozen.

Exact event settlement remains blocked: **13,524** original exchange-origin `markPrice` objects for 2022–2025 (9,144 before 2025; 4,380 in 2025), original official HTTP pages/headers, pagination, UTC timestamps, SHA256 and independently verifiable transport provenance. Official API access returned HTTP451 on hosted Linux/macOS; authorized exchange-origin export with chain of custody is the fallback. Existing V98 capture/audit/import tools cannot fabricate the missing evidence. **2025 is exposed training**, so untouched future prospective chronological validation and final holdout are still mandatory after a complete internal freeze. No 2026+ training, XRP, contaminated holdout, V14/V15/V99 internals/benchmarks, Frozen, V99 workflow/report/paper, or real trading was used or authorized.
