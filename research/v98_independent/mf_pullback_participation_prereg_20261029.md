# V98 MF — preregistered pullback compounding / volume participation dispersion portfolio (2026-10-29)

**PRE-RESULT FREEZE.** Economically distinct complete seven-slot portfolio from ME (breakout + downside asymmetry), MD (funding carry), MC (48h return reversal), MB (168h momentum RV), and all earlier rejected candidates. No rescue or retuning. Clean-4 BTC/ETH/BNB/SOL Binance USD-M 1h, 2022-12 warmup, 2023–24 training ONLY. 2025 validation, 2026+ holdout, XRP, Phase083, V14/V15/V99, Frozen and paper are inaccessible until eligible. Causal completed t -> next open t+1; signed native funding with pinned conservative official 1h worst-side mark envelope and two funding orderings; base 4/2bps, severe 10/10bps, supersevere 15/20bps.

## Seven fixed modules
1. **Growth Core:** every 504h from t=744, rank positive 504h returns by 504h log return / (0.08 + 4×168h downside semivol); BULL (>=3 positive 336h returns) long top two +0.55/+0.22 NAV; MIXED (1–2) +0.35/+0.12; BEAR cash.
2. **Opportunity:** every 168h in BULL/MIXED, among positive 336h return assets with negative 24h return, buy the most negative 24h (trend pullback, not breakout) +0.12 NAV for 168h, no same-clock reentry.
3. **Relative Value:** every 336h, compute quote-volume participation ratio = mean last 72h / mean preceding 264h for each asset, rank by ratio. If max-minus-min >0.10, long strongest relative participation and short weakest +0.06/-0.06 NAV for 336h. Mechanism is **cross-sectional liquidity participation**, not price return rank, funding carry, or downside skew.
4. **Stress/Recovery:** every 168h if >=2 assets have negative 336h return and at least one positive 24h return, long strongest positive 24h +0.09 NAV and short weakest 336h -0.04 NAV for 168h. Two-legged asymmetric recovery and hedge; no same-clock reentry.
5. **Regime Router:** BULL >=3, MIXED 1–2, BEAR zero assets positive 336h. Core and Opportunity gated; RV and Stress independently eligible.
6. **Dynamic Allocator:** reserve core then proportionally scale all optional sleeves to gross <=0.88 NAV; ablated capital remains cash.
7. **Risk Governor:** independently tested close-first causal atomic order planner, ex-ante cost/funding cash reserve, no future mark/rate sizing, intermediate gross <=100%, post-funding gross <=93%, positive intrabar worst equity.

## Fail-closed source-only gate
Independent three-sleeve calendar replay, zero mismatches, invalid entries and silent changes; synthetic/authenticated future-mutation pass, intended gross <=0.88; >=8 entries per sleeve per year in 2023 AND 2024. Failure irrevocably rejects MF before PnL.

## Physical 30-cell economic gate
Five books × base/severe/supersevere × two funding orderings, 17,543-hour physical each. Full base CAGR >50%, severe >30%, severe 2023 and 2024 returns positive, severe max DD <45%, base/severe turnover <= USD600,000 per initial USD10k, each sleeve marginal net log growth >0.02 base/severe and each annual marginal >=-0.03. Audit concentration, tails, PF/payoff/win rate, positive days, signed costs/funding, reproducibility. Reject on any gate; no post-result threshold/sign/window/gross adjustments.

If provisional training passes, freeze MF before independent all-hour PnL ledger oracle, cross-environment, severe corner tests, separate 2025 chronological validation, untouched future holdout and only then external benchmark comparison. No trading authorization.
