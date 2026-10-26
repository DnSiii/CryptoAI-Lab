# V99 I1 — invalid exchange-clock last-arrival revocation, original-source CI (2026-10-26 13:46 BRT)

**SOURCE_ONLY/HOLD — NO PROMOTION.** Concrete source-integrity defect fixed, not an economic trading result.

## Precommitted defect and correction
Preregistration commit `2229d5be70a59a80f7daa6a5f64407e5f022ee6f` predates changes to both the primary source join and the independently implemented raw-byte oracle. Both previously discarded quotes with exchange event time **later than their local physical arrival** before selecting the last physical update. That could resurrect a stale earlier executable book. Both now retain all original rows in capture order and select the most recent physically arrived predecision quote for each exact symbol **before** validating the exchange clock. An impossible newer event revokes the earlier book. Future physical arrivals cannot revoke.

Commits: `37eb7af8` primary join; `66ec588a` independent oracle; `bcb27cd5` two adversarial regressions; `349d6abc` full-history preregistration ancestry CI fix. No frozen artifacts, paper, champion, dashboard, validation, holdout or orders changed.

## Actual GitHub execution
- GitHub Actions [40362158259](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40362158259) **SUCCESS**, final branch code `349d6abc`. 11/11 adversarial tests passed, including two new invalid-clock revocation regressions on both implementations. The preregistration ancestry check passed.
- Original archived OKX spot + Deribit DVOL recomputed 182/182 TRAIN causal signal observations independently; original 4,000 partial Deribit option quote rows reparsed with SHA verification and rejoined. **132 positive causal indications; 0/182 source-ready synchronized asset-weeks; 0 intersections; 0 complete option lifecycles certified.** Independent oracle matched and rejected forged intersection and source SHA.
- Intermediate push-triggered runs before the workflow full-history fix failed on shallow preregistration ancestry, not market economics; only final run 40362158259 is the authoritative result.

## Exact remaining dependency
No licensed and independently verified **2021-12-09..2023-09-30 BTC+ETH Deribit options** full original BBO and size with venue event and physical arrival clocks, complete 21–45-day entry/mark/exit/settlement history, dated native lot/contract size, account fee tier, settlement index/TWAP, margin, maintenance and liquidation rules, plus credible execution/fill assumptions. Existing original 4,000 quote sample is insufficient. An explicitly licensed full-history Tardis Business export, CoinAPI original files, or equivalent Amberdata archive with verified 2021 availability and fields is acceptable. Vendor license/grant and actual SHA-identifiable source bytes must be supplied; synthetic fixtures or CI success cannot replace them.

**No original option economic TRAIN, no ROI, no promotion, no orders.** Preserve validation [2023-10-01,2024-01-18) and final holdout >=2024-01-18 sealed; do not retry rejected C1.