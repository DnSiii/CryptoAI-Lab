# V98 MD — preregistered slow carry-dispersion / growth compounding portfolio (2026-10-29)

**PRE-RESULT FREEZE.** New complete seven-slot engine, economically distinct from rejected MC contrarian 48h RV and MB 168h momentum RV. MC/MB/MA/LZ and all rejections remain permanently frozen, not retuned or transplanted. Authenticated Clean-4 BTC/ETH/BNB/SOL Binance USD-M 1h Dec-2022 warmup and 2023–24 TRAINING ONLY. No 2025+, XRP, Phase083, V14/V15/V99, holdout or paper. Next-open t+1 execution from completed t only. Signed native funding with pinned official 1h worst-side mark envelope (not exact tick), two funding orderings. Costs base 4/2bps, severe 10/10bps, supersevere 15/20bps.

## Fixed complete architecture and economic hypothesis
1. **Growth Core:** every 672 completed hours from t=744, rank positive 672h log-return assets by 672h return / (0.08+3×336h hourly downside semivol). BULL breadth of positive 336h returns >=3: top two long 0.52/0.24 NAV; MIXED breadth 1–2: top two long 0.40/0.12; BEAR: cash. Only positive 672h ranked assets.
2. **Opportunity:** every 336h, BULL or MIXED with >=2 positive 336h returns; positive 336h and 72h return, 72h quote-volume mean > prior 264h quote-volume mean, long highest positive 72h return at +0.14 NAV for 336h. No same-clock reentry.
3. **Relative Value:** every 168h, use ONLY completed 168h native funding history (21 known events). Rank assets by mean 8h signed funding rate; long lowest and short highest, +0.07/-0.07 NAV, only if historical funding differential >0.00015 per 8h and their 168h log-return gap <0.10. Hold 336h. Mechanism is **slow cross-sectional funding carry dispersion**, not price momentum or 48h reversal. No same-clock reentry. Historical spread is not guaranteed future carry.
4. **Stress/Recovery:** every 168h, if >=2 negative 336h returns and >=2 positive 72h returns, long strongest positive 72h recovery +0.12 NAV for 168h; no same-clock reentry.
5. **Regime Router:** 336h positive-return breadth BULL >=3, MIXED 1–2, BEAR zero. Core and Opportunity gated; RV and Stress allowed independent of breadth.
6. **Dynamic Allocator:** core reserved first; optional sleeves proportionally scaled to gross <=0.88 NAV, no reallocation of ablated sleeve capital.
7. **Risk Governor:** existing independently tested causal atomic close-first planner, ex-ante fixed 3% funding event reserve, no future mark/rate for sizing, intermediate gross <=100% NAV, post-funding <=93%, positive worst intrabar equity.

## Pre-PnL source-only gate
Independent replay of three entry calendars, zero mismatches/invalid/silent updates, synthetic and authenticated future mutation, max intended gross <=0.88 NAV, >=8 entries per optional sleeve per year 2023 AND 2024. Failure = irrevocable source rejection, no rescue.

## Physical 30-cell gate
Full, core-only, minus Opportunity, minus RV, minus Stress × base/severe/supersevere × two signed funding orderings. Full base CAGR >50%, severe >30%, severe 2023 and 2024 annual return positive, severe max drawdown <45%, turnover base/severe <=USD600,000 per USD10k, each optional sleeve marginal net log growth >0.02 base/severe and annual marginal >-0.03. Record tails, concentration, CVaR1%, PF/payoff/win rate, positive days, exact 30-cell arithmetic. No after-result sign/window/threshold/gross rescue.

If all training gates pass, freeze before independent all-hour ledger/settlement oracle, cross-OS and 81-corner, separate chronological 2025 validation, untouched future holdout, then external benchmarks. No live or guaranteed performance claims.
