# V99 H1 — ONE fixed options-implied forward-risk BTC/ETH spot/cash engine (2026-10-24 BRT)

**Preregistered before any H1 economic TRAIN PnL.** The earlier 6h trade-IV source contract failed 3/5; it is not reused. Independent original first-party Deribit **DVOL daily 30d implied-volatility index** passed 94/94 fixed weekly observations for both assets in all **5/5** chronological TRAIN folds at [Actions 40072202459](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40072202459), with Saturday completed daily candle (end strictly < Monday decision) and <=48h age. DVOL is a forward-looking market-implied *risk measure*, **not** an option executable bid/ask quote and not proof of return predictability.

## Distinct ex ante economic hypothesis and single fixed rule

**Hypothesis:** the option market's independently observed forward implied-volatility state can budget spot risk and temporarily avoid costly downside volatility shocks, unlike previously rejected price-trend C1, passive monthly beta E1, funding D1, basis F1 and expiring-future G1. H1 is **not** an E1 weight/parameter retune: it has an independent DVOL state variable and weekly causal risk allocation. It may fail economically and will then be permanently rejected.

- Exactly **94 fixed Mondays 00:00 UTC** in TRAIN [2021-12-09,2023-10-01), BTC-USDT and ETH-USDT **spot only**, no leverage, no shorts, no perp funding, no options trading. Initial capital 1.0 USDT-normalized.
- Monday decision `t` uses **only original DVOL weekly observations at t and the immediately preceding Monday** (both underlying Saturday candles closed strictly before their respective decisions). No previous Monday -> **100% cash**. If a DVOL input is missing/stale -> cash.
- **Shock veto:** if either `DVOL_t / DVOL_(t-1) > 1.20`, allocate **100% cash** for the coming week. **Absolute stress veto:** if BTC DVOL >=90 or ETH DVOL >=110 (annualized vol points), also cash. Otherwise allocate BTC weight `min(0.65, 0.35*(60/DVOL_BTC)^2)` and ETH weight `min(0.35, 0.20*(75/DVOL_ETH)^2)`; if total exceeds 0.90, scale both by `0.90/total`. Remaining equity stays cash. No retrospective threshold tuning.
- Execute Monday 00:00 **original first-party OKX spot open** at t, with exact self-financing cash/quantity/turnover/fee/slippage ledger; mark all **15,864 hourly TRAIN opens**, strict original grid. No trades between Mondays, no interest on cash.
- Four **modeled, NOT account-authenticated** fee/slippage scenarios per traded notional: severe 0.07%+0.05%, supersevere 0.14%+0.10%, severe shock 0.07%+1.05%, supersevere shock 0.14%+2.10%. Fee tier and historical fills not certified. No futures funding applies.
- Compare BTC-only buy-once, ETH-only buy-once, 45/45/10 buy-once and all-cash envelopes, under both main cost scenarios. 5 fixed chronological folds, strict t-1 3x2 BTC market direction/realized volatility regimes, compounded ROI, max DD, daily profit factor, best-day removal, worst day/week, top-five-positive-day concentration, full cost attribution.

## Hard TRAIN gates (all required before any formal freeze)
1. Severe ROI >0 and supersevere ROI >0.
2. >=4/5 severe positive folds and >=3/5 supersevere positive folds.
3. Both max DD >= -35%.
4. Both daily profit factors >1.
5. Both ROIs remain >0 after removing the best day.
6. Both worst daily returns >=-15%; both worst seven-day returns >=-25%.
7. Top five positive days account for <=60% of total positive daily gains in both scenarios.
8. Supersevere ROI exceeds fixed 45/45/10 buy-once supersevere by >=2 percentage points.
9. Original-source receipts, 15,864h self-financing accounting, all six regime partitions, two stress shocks, fixed benchmarks and **independent reexecution** must pass.

**If any gate fails, H1 is permanently REJECTED — NO RETUNE.** A passing modeled TRAIN is provisional only; formal freeze and independent native account fee/fill provenance are required before opening sealed validation [2023-10-01,2024-01-18). Final holdout >=2024-01-18 stays unopened until separate formal gates. No orders, no paper/Frozen/champion writes or PnL claims.
