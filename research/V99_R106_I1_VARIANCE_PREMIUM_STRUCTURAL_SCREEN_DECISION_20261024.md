# V99 R106 I1 — independently verified 30-day gross variance-premium structural PASS, EXECUTION BLOCKED (2026-10-24 BRT)

**Decision: I1 STRUCTURAL FEASIBILITY PASS ONLY — DATA_ONLY/HOLD — NO PROMOTION.** Not a complete trading engine, no after-cost return, no options fills, no realized or paper PnL, no validation or final holdout. This is a distinct **implied-minus-realized variance** economic mechanism, not H1's rejected DVOL directional spot allocation. No model or strategy is approved.

## Ex-ante, original-source execution
- Precommitted rules and five structural gates **before first execution** at [commit 89a88e4](https://github.com/DnSiii/CryptoAI-Lab/commit/89a88e4a248e42e87e55d0a0ea4c61322d6ea222).
- [Actions 40087572354](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40087572354) **SUCCESS**: recovered previously independently audited first-party original OKX BTC/ETH spot TRAIN opens (Actions 40019588739) and original Deribit BTC/ETH 30-day DVOL (Actions 40072202459); verified source bytes, hashes, timestamps, immutable five TRAIN folds and causal daily-candle availability; evaluated nonoverlapping 720-hour forward realized variance against 30-day implied variance.
- The first CI 40087555088 failed on shallow Git checkout of the preregistration ancestor, **before source loading or calculations**. Changed checkout to full history, then ran successful 40087572354; no economic threshold or strategy parameter changed.
- Independent implementation reconstructed all original source-to-window-to-variance-to-fold-to-gate values and rejected a deliberately corrupted realized-variance observation. Oracle status: `INDEPENDENT_ORIGINAL_DVOL_SPOT_30D_VARIANCE_REEXECUTION_VERIFIED`.
- Precisely **15 nonoverlapping 30-day windows per asset**, 3 per each of 5 folds (30 asset-window observations total). Weekly DVOL decisions were selected by fixed calendar and within-fold forward-window availability, never by forward realized returns. Five of five preregistered *structural* gates passed.

## Gross variance-information results (dimensionless variance, **NOT ROI**)

| Metric | BTC | ETH |
| --- | ---: | ---: |
| Average 30-day implied variance minus subsequent realized variance | **+0.01170168** | **+0.00934878** |
| Folds with positive average premium | **4/5** | **4/5** |
| Fold 1 mean premium | +0.00622465 | +0.00179493 |
| Fold 2 mean premium | **-0.00297497** | **-0.02946469** |
| Fold 3 mean premium | +0.03518962 | +0.05391160 |
| Fold 4 mean premium | +0.01462825 | +0.01720872 |
| Fold 5 mean premium | +0.00544084 | +0.00329335 |

Definition: `implied_var=(DVOL_percent/100)^2*30/365`, `realized_var=sum_{h=1..720}(ln(open[t+h]/open[t+h-1]))^2`. No option position was simulated. The positive signed aggregate is **sensitive to fold 3**: fold 3 alone accounts for about 60% of BTC's and 115% of ETH's net sum of fold mean premiums. These descriptive shares are not new pass/fail criteria. The 15 nonoverlapping windows/asset are a small sample and BTC/ETH are economically correlated; no statistically reliable net trading edge has been established. No severe/supersevere, portfolio NAV, max drawdown, tradable benchmark, tail PnL or independent *economic* validation was run.

## What exactly blocks an integrated, independently validated I1 engine
- Original Deribit DVOL is **an index**, not an executable 30-day option or variance swap price. An IV-minus-RV screen does not imply a tradeable short-volatility profit: option strikes/expiries, delta hedging, discrete gamma exposure, convexity, funding of collateral, margin, fees, adverse selection and settlement change the realized payoff.
- The sampled public historical option quote source yielded 4,000 updates, only 3,069 positive two-sided quotes, and full historical downloads **HTTP 403** without licensed entitlement (Actions 40083504198). Those few first seconds of two isolated days cannot support the 2021–2023 full TRAIN.
- Required external data contract: authorized historical executable BTC/ETH options L1/L2 bid/ask **and quantities** with both exchange and local-arrival timestamps, instrument IDs, strikes, expiry, contract size and quote-currency semantics, covering **2021-12-09 through 2023-09-30** with a gap/completeness manifest; applicable historical Deribit margin, collateral, expiry/settlement and account-specific fee tier; size-aware hedge execution and historical spot/perp costs, with actual settled funding if hedging with perps. Before paying, verify that the license explicitly covers **2021** and permits reproducible research use. Actual historical fills cannot exist for hypothetical unsubmitted orders; use transparent conservative execution models, never claim authenticated fills.
- Next *justified* engineering step once that coverage is verified: **one** preregistered, integrated delta-hedged short-volatility engine with cash/collateral/margin, bid/ask crossing, fees, dynamic hedges, gap/tail risk, five original chronological folds, severe/supersevere shocks, benchmark envelope, independent ledger and formal TRAIN gates. Only if it passes and is frozen may [2023-10-01,2024-01-18) validation be opened; final holdout remains gated. **Do not** retune based on fold 2, or reinterpret these variance values as ROI.

V16 Frozen, V99 Frozen, legacy champion, paper-results and public dashboard unchanged. No orders. **NO PROMOTION**.
