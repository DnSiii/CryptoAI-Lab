# V98 Independent Phase243 — 2026-10-12 20:48 BRT source-only audit

Scope: research/v98-independent-zero; V98-only, DATA_ONLY / NO_ALPHA; 2023–2025 training only. No 2026+ holdout, V16, V99 or paper changes.

## Independent source integrity
GitHub source-acquisition run 38053620316 failed at XRPUSDT-1h-2023-11 zero-based row 323 (2023-11-14 11:00 UTC). Source-only tests passed; canonicalization/funding stages were skipped. Rejected-source artifact 11670362663 was retained. No newer source-acquisition run was found in branch-filtered inventory.

## Preregistered XRP quote-volume contamination footprint
Input original Binance ZIP (provider SHA256 sidecar matches, not a signature): SHA256 `29b7a4a3b9360f7b3be131af6b1fd619f18e7344eea99b5c964e955e667027a7`. Exactly 720 November 2023 hourly bars, one invalid physical quote/base and seller-residual bar at 2023-11-14 11:00 UTC. Implied quote/base VWAP 0.8275064480 exceeds candle high 0.6556. **Conditional on base volume being correct**, minimum total quote overstatement is 10,663,858.09457 USDT and minimum seller-residual quote overstatement is 10,815,307.77033 USDT. The original field(s) in error cannot be determined, and no source value was repaired.

Using frozen causal quote-volume windows (current and previous hours, within month only): 1h affects 1/720 decision hours (minimum conditional overstatement 20.774% of observed 1h quote volume); 24h affects 24/697 full-window hours (range 0.4153–1.0383% of observed rolling quote volume); 168h affects 168/553 full-window hours (range 0.1319–0.2183%). This is a data-quality footprint, not alpha. The exact 1h bar is not independently authenticated by daily 1h/1m originals.

## Phase240 independent economic invariant audit
Audited committed `phase240_results.json` (Git blob `55c13167d1f29683a2a18c3a8e7a695ea090c4f9`): eight specs × three years × three cost regimes = 72 records. All 72 returns negative and all 72 Profit Factors <1. All 216 nested regime returns negative and PF<1. No violations in 72 tail quantile orderings, day bounds, numeric finiteness, win/positive-day ranges, drawdown bounds; all 24 spec-year pairs monotonic in return, PF and drawdown under base→severe→supersevere costs. Mean return by cost regime: base -0.9801894404; severe -0.9994075810; supersevere -0.9999993123. This rechecks published summaries only; no hourly ledger or new backtest was used.

## BNB native funding timing signature
From committed V98-only BNB funding CSV (Git blob `6b46a2a911d85079f3ce4ec5bc8b1791febd397a`), 3,288 training 8-hour slots, 1,800 exact zero rates. Zero counts by UTC settlement hour 00/08/16: 2023 169/162/176, 2024 196/188/198, 2025 236/240/235. Persistence (within-year zero→zero counts) 385 in 2023, 490 in 2024, 558 in 2025; longest run 77 slots. No clear single settlement-hour-only gap mechanism, but these patterns cannot authenticate exchange funding.

## Decision
Phase240 REJECT_FAMILY_NO_RESCUE. Phase243 BLOCKED_SOURCE; champion NONE. No holdout access, source repair, alpha backtest or promotion. Offline V98-only source footprint auditor and adversarial tests are preserved in cycle evidence package; remote publication of the code is pending. Next priority: capture publisher-checksum-verified XRP daily 1h and 1m originals for 2023-11-14, reconcile all 24/1440 rows and independently authenticate BNB raw funding provenance. Preserve chronological folds, costs/funding, severe/supersevere, regimes, concentration/tails, max drawdown, Profit Factor, payoff, win rate, positive days, and reproducibility.
