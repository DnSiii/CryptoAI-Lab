# V98 Independent — Phase243 funding concentration / tail audit (2026-10-08, 17:52 BRT)

**Scope:** V98-only Phase206 native funding CSVs; five fixed assets; 2023-01-01 inclusive to 2026-01-01 exclusive. No 2026+ holdout, external engine, market-price PnL, model selection, or candidate promotion. This is **DATA_ONLY / RISK_ONLY**, not a backtest.

## Independently checked source integrity
Each of BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, SOLUSDT has **3,288** consecutive 8-hour training settlements, hence **16,440** total. All five pass timestamp UTC/ms equality, strict monotonicity, 8-hour scheduled-slot coverage, 8-hour interval field, and <2026 firewall. Exactly **1,054 jittered timestamps per asset** (5,270 total), maximum **29 ms**; scheduled boundaries rather than literal reporting milliseconds are the correct settlement keys.

Git blob identifiers of audited files, respectively: BTC `50732b1fb26c748ffeea9fa97e71626eaef89544`; ETH `bde2ff02f21d7369cbfeecc339224594cc0b7591`; BNB `6b46a2a911d85079f3ce4ec5bc8b1791febd397a`; XRP `c61589ead8f0f7a86c51a6202a476b765b537eb4`; SOL `3c1ef787ef7ae4ec731284962ee853b7fd882ebd`. SHA-256 raw CSVs should additionally be frozen by the existing V98 source auditor before real PnL.

## Extreme funding and concentration (training-only)
Absolute per-event thresholds are **7 / 14 / 28 basis points**; a basis point is 0.0001 of notional. Counts of events above these thresholds:

| Asset | >7 bp | >14 bp | >28 bp | Max absolute event | Longest consecutive >7 bp |
|---|---:|---:|---:|---:|---:|
| BTC | 7 | 0 | 0 | 8.8148 bp | 2 |
| ETH | 5 | 0 | 0 | 10.1724 bp | 2 |
| BNB | 96 | 9 | 0 | 20.8684 bp | 15 |
| XRP | 15 | 0 | 0 | 11.0000 bp | 4 |
| SOL | 40 | 10 | 6 | 92.7078 bp | 7 |

A fixed **short** notional position on SOL would pay a cumulative **293.6545 bp** of funding over its worst observed eight consecutive settlement events, starting 2023-01-02 16:00 UTC (about 64 hours); BNB short worst eight-event debit was **117.8396 bp** starting 2023-03-20 00:00 UTC. A fixed **long** position on SOL had a worst eight-event debit of **63.3955 bp**. These are *funding-only notional debits* without price PnL, fees, leverage, liquidation, or dynamic allocation; **they are not strategy returns**.

The largest SOL event, -92.7078 bp, occurs at scheduled 2023-01-04 08:00 UTC; assigning funding by exact-hour-only records would miss it. This one-event absolute magnitude exceeds the **28 bp** supersevere per-turnover-unit fee stress, but the quantities are not directly additive without the actual trade and exposure path.

## Descriptive time-clustering diagnostic, not a promotion test
With a **fixed 7 bp absolute threshold** and 2,000 deterministic random permutations per asset of the same 3,288 event indicators, observed longest extreme-event runs were BTC 2, ETH 2, BNB 15, XRP 4, SOL 7. Longest runs in shuffled sequences never exceeded 2, 2, 4, 2, 3 respectively. Exploratory smoothed permutation exceedance estimates: BTC 0.01099, ETH 0.00550, BNB 0.00050, XRP 0.00050, SOL 0.00050. This null deliberately destroys serial dependence and seasonal regimes; it is **not** a realistic market null, not confirmatory statistical evidence, and must not be used to tune thresholds or select V98 strategies.

## Accounting consequence and mandatory next gate
Real historical prices are **not present** under the repository's `data/canonical` directory at the audited branch; therefore no honest Phase243 integrated historical PnL can be claimed from this funding-only evidence. Obtain and SHA-freeze the five canonical OHLCV files, run the V98-only price integrity gate, then integrate the *pre-registered* funding schedule with exact self-financing turnover and terminal liquidation on 2023, 2024, 2025 chronological training folds. Evaluate 7/14/28 bp costs, funding-boundary sensitivity, PF, payoff, MDD, positive UTC days, tails, concentration, regimes, deterministic rerun and anti-overfit gates. Do not open holdout or consult other engines.

## Workflow distinction
The latest completed V98 research workflow run 37827605449 was successful operationally but concerned Phase142/143/144, **not** Phase243. Phase142 and Phase144 were rejected by their frozen gates; no promotion follows from workflow success.

**Decision:** DATA_ONLY funding integrity PASS; significant descriptive tail/clustering risk; **Phase243 real-system evaluation NOT RUN; champion unchanged / none promoted**.
