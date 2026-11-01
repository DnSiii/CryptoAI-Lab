# V98 PF — frozen full-history rejection and source-integrity improvements (2026-11-01)

**Binding decision: REJECT_PF_TRAINING permanently.** PF is not a champion, internally validated engine, paper PnL or live trading authorization. No post-result sign, weight, window, threshold, gross, fee, funding or sleeve rescue.

## Preregistered architecture and reproducible execution
- [PF preregistration](pf_causal_counterfactual_allocator_prereg_20261101.md) was committed as `be0a0b02ababdb1ac181801ac965e8969e63d789` **before** PF strategy code, data-backed PnL and binding gate result.
- Seven-slot PF used independently specified growth core, opportunity, beta-neutral RV, stress/recovery, regime router, causal 8-week net-contribution allocator and risk governor. No rejected candidate signals/parameters, external V14/V15/V99 benchmark or future 2026+ data used.
- Complete historical 30-cell source-gated run [Actions 41278345870](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41278345870), pinned executable commit `4ab9b6779b8e3f2c957c05c2b208df69f5c23a51`. The workflow's **failure exit is intentional economic rejection**, not a data/runtime failure. All **30/30 physical cells passed**.
- The complete unselected `PF_RESULT_JSON` receipt is frozen at [PF 30-cell JSON](pf_full_training_frozen_result_20261101.json). Independent scalar decision/score/allocation oracle: 157 decisions, 5 books, 0 mismatches, max error 8.05e-15. Independent cash identity: 26,303 hours, 0 mismatches. Independent fill/funding/fee oracle: 220 net fill events, 0 mismatches. Separate [independent 30-cell arithmetic and binding-gate replay](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41278437600): **60/60 arithmetic checks correct; 28/28 economic gate failures independently reproduced**.

## Physical simulated economics (carried-before-fill)
| Full PF | Base | Severe | Supersevere |
|---|---:|---:|---:|
| Simulated CAGR | +13.03% | +8.83% | +4.49% |
| Maximum drawdown | -35.44% | -36.53% | -37.68% |
| Turnover on initial USD10k NAV | USD931,219 | USD876,237 | USD821,763 |
| 2024 net annual return | +2.16% | -1.99% | -6.26% |

Full-minus-ablation marginal log-growth under base: Opportunity **-0.04257**, Relative Value **+0.02944**, Stress/Recovery **-0.04141**. Under severe: Opportunity **-0.04252**, RV **+0.01301**, Stress **-0.04238**. RV severe falls below the preregistered +0.02 floor; Opportunity and Stress destroy marginal growth in both tiers. Full PF base CAGR +13.03% < core-only +15.43%; full seven-slot composition does not earn its capital. The severe 2024 loss also fails the positive-year gate. **28 binding failures** total; no promotion.

## Source provenance and no-2026 scope hardening in same cycle
- Hardened existing `v98_exact_funding_full_history_ingest.py` to reject coerced/float/bool funding timestamps/values and to demand an **exactly bounded** official Binance request query: symbol, 2022-12 through 2025-12 event end, limit=1000; no duplicated/extra params or 2026+ end-time claims.
- Hardened existing `v98_exact_funding_full_history_capture_audit.py` to reject missing/non-JSON HTTP headers, non-UTC/reversed or nonsequential request/response chronology, noncanonical page/asset filenames and raw-chain aliasing.
- Existing isolated [full-history content-contract Actions 41278215969](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41278215969) passed: 15 strict importer synthetic tamper cases, 5 capture tamper cases, 5 independent page-chain tamper cases. These tests **do not acquire official data or attest exchange origin**. A redundant workflow introduced briefly was removed; the preexisting contract workflow was reused.

## Exact unresolved release gates
The authorized Binance USD-M funding history capture remains blocked by HTTP 451 on hosted Linux/macOS. Missing **13,524 original event-level `symbol,fundingTime,fundingRate,markPrice` objects** (3,381 per Clean-4 asset) with raw official HTTP bodies, pagination URLs, request/response UTC chronology, response headers, SHA256 and independently verified lawful exchange-origin/transport evidence. Alternative: an authorized exchange-origin export from a permitted network with verifiable chain of custody, then run the existing full-history capture audit and native-rate/mark-envelope importer. Native signed funding rates and conservative official hourly mark-price envelopes already exist, but are **not exact funding-tick settlement**.

Independently of this external source blocker, **no complete seven-slot V98 candidate passes internal economic gates**, and an untouched chronological prospective validation/final holdout remains outstanding. The exposed 2025 period is not an independent holdout. Next useful research must identify a **genuinely new, authenticated economic return source** with full Clean-4 coverage before more complete-system preregistration; do not cosmetically repeat rejected OHLCV/funding proxies. No V16/V99 Frozen, V99 research, paper, external benchmark or 2026+ data modified or used.
