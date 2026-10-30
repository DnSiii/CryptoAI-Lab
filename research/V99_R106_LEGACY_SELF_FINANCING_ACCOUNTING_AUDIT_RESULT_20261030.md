# V99 R106 — 2026-10-30 legacy C1/C2 self-financing accounting audit: REAL TRAIN result, NO PROMOTION

## Decision
**ACCOUNTING DEFECT CONFIRMED in the old modeling convention; C1/C2 remain PERMANENTLY REJECTED.** This is a read-only audit of historical TRAIN target journals, not a new economic strategy trial, not a fix to archived C1/C2 outcomes and not an exchange-certified PnL claim. The reusable quantity-based conservation checker is in `research/tools/v99_r106_legacy_self_financing_audit.py`.

**Evidence:** preregistered before code in `research/V99_R106_LEGACY_SELF_FINANCING_ACCOUNTING_AUDIT_PREREG_20261030.md` (commit `f981e76f0f475af82e3bd6916d6853c93d0bfff7`). GitHub Actions first original execution [41057673743](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41057673743) SUCCESS. Follow-up run [41057812142](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41057812142) SUCCESS with explicit historical C1/C2 ROI integrity checks. 9/9 adversarial synthetic tests passed; actual canonical BTC/ETH TRAIN cache restored; two full read-only original replay outputs were byte-identical; original journal oracles and the new independent conservation equations passed. Artifact: [read-only JSON evidence](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41057812142/artifacts/12978176313).

## Critical accounting finding (actual archived original TRAIN sources)
The old journal computes transaction fee from `sum(abs(target_weight_t - target_weight_t_minus_1))`. If a target weight is intended to be maintained **every hour**, contract quantities must be rebalanced after the market price and portfolio NAV drift; a constant target weight does not imply zero executed turnover. The new diagnostic replays the unchanged target journals with signed contracts, variation-margin PnL, exact implicit fee and a second algebraic NAV/position conservation check.

| Rejected system / cost | Original weight-delta turnover sum | Quantity-based turnover / pretrade NAV sum | Difference | Legacy zero-turn hours with nonzero required quantity rebalance |
|---|---:|---:|---:|---:|
| C1 severe | 163.938109 | 206.488926 | **+25.96%** | 12,737 |
| C1 supersevere | 156.814925 | 201.297460 | **+28.37%** | 12,819 |
| C2 severe | 17.428349 | 34.190327 | **+96.18%** | 15,840 |
| C2 supersevere | 17.428349 | 34.188591 | **+96.17%** | 15,840 |

Each row covers **16,055 actual original TRAIN hourly target observations**. The turnover quantities are normalized differently but are directly comparable as sums of per-hour notional / equity ratios under the stated hourly-rebalance convention. The comparison is **conditional on holding the original journal target weights at each hour**; it does not establish how an actual exchange would have filled orders. No original C1/C2 file, result, gate or model was edited.

### Important qualification
- The legacy engine does not unambiguously specify whether its hourly weights are **continuously rebalanced targets** or **initial holdings allowed to drift**. The table proves the legacy *fixed-hourly-weight + zero-drift-fee* accounting cannot represent both at once. An alternate no-trade/buy-and-hold policy would have **different weights and risk paths** and needs its own ex ante strategy specification. Do not mechanically present the table as a certified actual cost underestimate.
- C1 is path-dependent: a changed fee/NAV would change the drawdown governor's later decisions. The conditional revaluation is **NOT a corrected valid C1 strategy PnL** and may not be used to retune/revive C1. C2's fixed path is also a retrospective rejected strategy, not a candidate.
- No authenticated historical funding settlement, fee tier, spread/depth, fill, margin or liquidation evidence is added by this audit. No valid forward paper or real-money profitability follows from GitHub CI success.
- Both historical C1/C2 negative outcomes were independently rechecked against the published 2026-10-16 TRAIN rejection ROI values (within report rounding). Both systems **still fail original TRAIN gates**.

## Next actual critical path
Any genuinely new preregistered integrated architecture must first choose and enforce **one** execution convention (contract carry + explicit rebalance schedule vs continuously targeted weights), then bind quantity-based native fees, settled funding, fill/depth, margin/liquidation and causal risk accounting to the same portfolio NAV. Validate all five chronological TRAIN folds, both severe/supersevere scenarios, 3x2 regimes and tails before considering frozen independent validation. Do not open sealed validation `[2023-10-01, 2024-01-18)` or final holdout `>=2024-01-18` for a failed or unregistered candidate.

**External I1 blocker unchanged:** lawful original Deribit BTC/ETH options bid/ask, size/arrival, marks and expiry/delivery tape for the missing **658 of 661 days**, with independently verifiable checksums, license and dated fee/margin/settlement terms. Public trade prints do not substitute for executable two-sided quotes. The Binance funding API HTTP 451 and missing historical bookTicker HTTP 404 are separately recorded source limitations, not license to fabricate. Continue independent engineering without treating those missing sources as present.

**NO PROMOTION / NO NEW ECONOMIC CANDIDATE / NO REAL ORDERS / NO PAPER CHANGE / NO FROZEN CHANGE / HOLDOUT UNOPENED.**
