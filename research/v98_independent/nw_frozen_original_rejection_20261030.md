# V98 NW — original frozen economic rejection (2026-10-30)

**REJECTED PERMANENTLY.** New price-structure seven-slot hypothesis was preregistered before NW PnL at commit `8c66a8ab1b39233bde16ca9b5e23bc3122f7ad74`, implemented at `50a02c585b876972856ad77202af5515ee6d7411`. No post-result sign, window, threshold, gross, funding or gate rescue permitted.

**Original physical evidence:** GitHub Actions [41146144426](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41146144426), run head `50a02c585b876972856ad77202af5515ee6d7411`. Workflow failure is **intended binding economic rejection**, not a failed physical engine. Clean-4 2023-24 development only; exact funding mark still unverified.

**Measured carried-before-fill full engine, per USD10k initial equity:**
- Base CAGR +30.0950%, max DD -45.4629%, turnover $687,189.56; 2023 +79.9339%, 2024 -5.9054%.
- Severe CAGR +26.0435%, max DD -46.2014%, turnover $664,292.65.
- Supersevere CAGR +21.8263%, max DD -46.9843%, turnover $640,729.48.
- Base marginal log-growth: Opportunity +0.016463, Relative Value +0.023320, Stress/Recovery +0.000000.
- Opportunity raw activation: 1/26 decisions in 2023, 0/27 in 2024. RV: 14/26 and 16/27. Stress: 0/26 and 0/27.
- **20 frozen economic failures** across base/severe and both funding orders: growth, turnover, severe DD, negative severe 2024, Opportunity marginal below floor, Stress marginal zero. No economic approval.

**Technical evidence:** source-only 53/53 decisions independently recomputed, zero mismatches; 9,144 signed 8h funding events; 30/30 physical cells passed invariants; 17,543 hourly signed settlement rows independently reconciled; 17,543 strategy-to-fill rows independently checked, 144 rebalances, zero quantity mismatches, synthetic fill tamper detected; 30-cell arithmetic and economic gates independently reproduced. These attest execution/accounting of a rejected strategy, not trading edge.

**Outstanding source dependency:** four official or independently authenticated per-symbol files with `symbol,fundingTime,fundingRate,markPrice` (2,286 rows each, 9,144 total, Dec 2022–Dec 2024), with transport/source attestation. Official Binance USD-M `/fapi/v1/fundingRate` documents event `markPrice`, but original access HTTP 451, alternate HTTP 202 empty, third-party timeout. Signed worst-side hourly mark envelope is conservative but not exact funding settlement. Missing exact marks did not cause NW economic failure.

**Scope:** 2025 already exposed to earlier candidates, not fresh validation. 2026+ future holdout untouched. No external-engine internals, no Frozen/V99/paper changes, no live authorization.
