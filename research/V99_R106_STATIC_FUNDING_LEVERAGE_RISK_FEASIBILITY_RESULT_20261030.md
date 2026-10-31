# V99 R106 — static funding-only notional/risk sensitivity (2026-10-30 21:54 BRT)

**SOURCE_ONLY / NO PROMOTION. This is NOT a new complete engine, historical ROI, a trading recommendation, realized paper or exchange-certified funding cash.**

## Ex-ante protocol and actual CI
- Fixed source-only math [preregistered BEFORE implementation](V99_R106_STATIC_FUNDING_LEVERAGE_RISK_FEASIBILITY_PREREG_20261030.md) at [commit 8d6aa536](https://github.com/DnSiii/CryptoAI-Lab/commit/8d6aa536558dca3a86970b432dc2f3a7b8386b8b).
- [GitHub Actions 41152529159](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41152529159) **SUCCESS**, 6/6 adversarial synthetic software tests. It then **actually re-downloaded and publisher-SHA256-verified all 44 original Binance ZIPs**; existing independent original-byte oracle reconstructed 1,983 funding events per BTC/ETH asset and all five immutable TRAIN folds. A separately implemented second oracle rechecked the new notional/risk arithmetic from the original-ZIP-derived source oracle, independent of the primary new calculator. No sealed validation, final holdout or historical PnL evaluated.
- Redacted CI artifact: **13023189075**, digest `sha256:e6cf76df14812b896dd8398329f89a3ac7153a050e481f587edf2bbe7daff2e4`. Original ZIP/CHECKSUM bytes removed before artifact upload.

## Fixed illustrative linear funding-only sensitivity, NOT NAV

The preregistered hypothetical target was **+100 percentage points of initial equity as a *nominal funding budget***, deliberately NOT a claim of 100% portfolio return. The 50/50 short-perp rate budget, original first-party Binance published funding rates, and the fixed severe/supersevere four-side cost allowance per fold are identical to the earlier [source-only mechanism screen](V99_R106_BINANCE_STATIC_FUNDING_BUDGET_MECHANISM_RESULT_20261030.md). No strategy was fitted or retuned.

| Metric | Severe modeled allowance | Supersevere modeled allowance |
|---|---:|---:|
| 661-day sum of five illustrative cost-adjusted nominal rate budgets, NOT ROI | **6.436126%** | **5.036126%** |
| Positive nominal-budget TRAIN folds | **4/5** | **4/5** |
| Notional/equity multiple required to reach +100pp *linear nominal budget*, NOT portfolio ROI | **15.5373×** | **19.8565×** |
| Residual adverse basis/hedge error shock corresponding to 35pp initial-equity erosion, purely first-order | **2.252644%** | **1.762644%** |
| Residual adverse basis/hedge error shock corresponding to 100pp initial-equity erosion, purely first-order | **6.436126%** | **5.036126%** |
| Weakest fold nominal-budget contribution at the illustrative multiple, NOT NAV | **−0.9924pp** | **−6.8281pp** |

**Interpretation:** the original funding-only static budget is small enough that matching a nominal +100pp equity target would require ~15.5–19.9× initial equity in constant hypothetical gross notional, before basis path, fills, real fees, native funding cash settlement, margin, liquidation, collateral haircuts or market-impact. At those hypothetical multiples, an adverse residual basis/hedge error of only ~1.76–2.25% corresponds arithmetically to a 35pp equity loss. These are *sensitivity calculations*, not historical price shocks, real margin thresholds, VaR, exchange liquidation estimates, or predictions. A dynamic alternative could differ; this is NOT an impossibility theorem for every carry strategy.

The negative third fold remains negative under both illustrative cost paths. Neither a successful CI nor 4/5 positive *rate budgets* is evidence of a profitable integrated portfolio. This result **weakens the rationale for spending the next cycle constructing another leveraged funding-only variant solely to chase high growth**; it does not justify resurrecting the permanently rejected D1/D2 or promoting a new candidate.

## Decision and critical path
**NO PROMOTION. No new economic candidate, no ROI, no full TRAIN NAV, no native fill/fee/margin certification.** Stop using funding-only rate budgets as evidence of high-growth profitability. Prioritize an independently source-backed, genuinely distinct complete-system mechanism with a clear causal edge and fully specified native execution/cost/margin before any preregistered economic TRAIN. The I1 options path still needs a dated lawful vendor entitlement, full 2021-12..2023-09 BTC+ETH two-sided executable option quote/depth/size/arrival archive (**658/661 quote days missing**), original fee/settlement/margin terms and independently verified lifecycle replay (**0/180 certified**). Public Deribit trade prints do not substitute for BBO.

V16 Frozen, V99 Frozen, paper/results, legacy champion, sealed validation [2023-10-01,2024-01-18), final holdout >=2024-01-18 and all order systems untouched. No orders placed.
