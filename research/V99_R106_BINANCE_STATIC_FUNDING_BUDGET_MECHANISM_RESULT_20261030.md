# V99 R106 — original Binance funding-rate budget mechanism result (2026-10-30 19:56 BRT)

**Decision: STATIC FUNDING BUDGET UNFALSIFIED IN 4/5 FOLDS, BUT NOT AN ECONOMIC CANDIDATE. SOURCE-ONLY / NO PROMOTION.**

## Preregistered and actually executed
- Ex-ante mechanism contract was committed BEFORE code and new source replay at [baaaf2d](https://github.com/DnSiii/CryptoAI-Lab/commit/baaaf2daa0253d32270ddf2e92dcb2ae4cfa77cb). No parameter search, no change to any rejected D1/D2/D3/C1/C2/S1.
- [Actual GitHub Actions 41141154519](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/41141154519) **SUCCESS**: 6/6 adversarial tests, **44/44 original Binance publisher-SHA256 ZIPs**, **1,983 original funding events per BTCUSDT and ETHUSDT** in the strictly isolated [2021-12-09,2023-10-01) TRAIN, 5 chronological folds. Native archive calc_time +0..31ms was bound only to retrospective event time, NOT used as a tradable early observation.
- The separately implemented original ZIP/CHECKSUM-byte oracle independently reconstructed all rates, five folds, signed rate sums and fixed cost-budget arithmetic to <=1e-12, and agreed with the primary. Publisher ZIP manifest SHA256: `48712069b1e576764f518928077ca7fc7ffa1498a9aa9fa3372890500e9de175`. Source-only redacted Actions artifact: **13017839340** (digest `sha256:ccecc0f41477ec53fd8f3817a45798d226859e6665ed4851f6ff5c2219b2dd5f`). Raw ZIPs/CHECKSUMs deleted before upload.

## Measured ORIGINAL PUBLISHED FUNDING-RATE BUDGET (NOT ROI, NOT ACCOUNT CASH)

| Chronological TRAIN fold | BTC signed rate sum | ETH signed rate sum | 50/50 short-perp signed funding budget | After illustrative severe 0.28pp | After illustrative supersevere 0.56pp |
|---|---:|---:|---:|---:|---:|
| 1 | +2.198448% | +1.888448% | +2.043448% | +1.763448% | +1.483448% |
| 2 | +1.469005% | +0.520762% | +0.994884% | +0.714884% | +0.434884% |
| 3 | +1.278132% | -0.845873% | +0.2161295% | **-0.0638705%** | **-0.3438705%** |
| 4 | +2.631921% | +2.794982% | +2.7134515% | +2.4334515% | +2.1534515% |
| 5 | +2.023890% | +1.712537% | +1.8682135% | +1.5882135% | +1.3082135% |

**Source-only decision:** 4/5 illustrative cost-adjusted *funding-rate budgets* are positive in both severe and supersevere. The whole 661-day original TRAIN static 50/50 signed nominal-rate budget sums to **0.07836126 (7.836126 percentage points of hypothetical constant notional)** before all fees and basis moves. Subtracting the preregistered one theoretical four-side hedge roundtrip *per fold* gives **0.06436126 severe** and **0.05036126 supersevere** over the five folds. These are **NOT compounded portfolio returns**, nor evidence of realized funding or executable profit. The illustrative cost convention is not an account fee schedule.

## Economic interpretation and binding next step
This is a real source-backed mechanism feasibility finding: the static funding-rate *budget* is not falsified by the 4/5 fold prerequisite. **It is NOT proof of high-growth alpha.** The gross budget of only 7.84 nominal-rate points over 661 days is modest for the V99 high-growth objective even before basis changes, actual fills, margin, liquidation, native fees, funding cash settlement and risk; the third fold fails both illustrative cost allowances. A hedged perp/spot strategy may lose substantially despite positive funding-rate sums. No full strategy was created, no historical price-to-cash NAV was simulated, and the previous D1/D2/D3 permanent rejections remain binding. Do not promote or resurrect them.

**Next shortest justified step:** do NOT serially retune price thresholds or preregister a passive carry engine just because this source-only budget is positive. Before any new complete-system candidate, establish a genuinely distinct, source-backed, economically meaningful expected-return mechanism with native dated fee/margin/collateral, executable size-aware spot/perp BBO and actual funding-settlement semantics; only then preregister one complete strategy and run original fivefold TRAIN with 3x2 regimes, two cost paths, shocks, tails/DD, independent NAV and benchmark gates. The existing I1 option-volatility alternative still lacks a dated lawful 2021–2023 vendor entitlement, **658/661 original Deribit quote days**, original executable bid/ask/size/clock and delivery/fee/margin terms; 0/180 lifecycles certified. An authenticated equivalent vendor archive is an alternative, but no blind purchase is justified.

**NO PROMOTION / NO ORDERS / NO ROI / NO PAPER / NO VALIDATION / NO HOLDOUT.** V16 Frozen, V99 Frozen, legacy champion, public performance records and rejected candidates unchanged. [Read-only branch diff e05a5ca..d698f2f](https://github.com/DnSiii/CryptoAI-Lab/compare/e05a5cad8580dc754435c120d7d92bc4a428a67c...d698f2f44522c66d361e527230aa41d57a92332d) adds exactly 5 research/CI paths, no existing files modified.
