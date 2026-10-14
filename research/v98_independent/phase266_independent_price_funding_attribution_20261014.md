# V98 Independent Phase266 — independent price/funding attribution (2026-10-14)

**Scope:** branch `research/v98-independent-zero`; V98 only; Clean-4 BTC/ETH/BNB/SOL; 2023–2025 training, 2022-12 warmup. No 2026+, no Phase083 holdout, no V14/V15/V99. This is **NOT** an official native Phase266 backtest or promotion decision.

## Frozen hypothesis and provenance

The previously locally preregistered Phase266 rotates +0.125 BTC against -0.125/3 in each ETH/BNB/SOL on CFTC short crowding, with 23:00 UTC close decisions and next 00:00 UTC execution. Source Phase264 CSV SHA-256 `6b2a01f06db2b95c8eec97862730b61b7c6033692dc79e216472095707d8be7d`; Phase265 availability ledger SHA-256 `efd159d201aca666898cc5a971c33aca95215f3c518356b3b14054050d03ca36`; Phase266 events SHA-256 `8a3a001b94a8ddc905c875c6233267f9e44f064cf15dd85727e400afe3d23959`. Local reruns reproduced both ledgers byte-for-byte; 27 source tests and 6 independent attribution tests passed.

## Independent diagnostic (NOT compounded portfolio PnL)

Seven ON intervals / 14 transitions / 204 days / 4,896 active hours. Exact Clean-4 1h open-price SHA-256 verified against source manifest. Open-to-open **linear overlay price contribution**: +0.54307% of reference equity, comprising 2023 -1.65437%, 2024 +1.04359%, 2025 +1.15385%. Overlay turnover approximation 3.5 L1. The three per-side fee tiers imply 0.245%, 0.420%, 0.700% equity cost, respectively.

Independent native V98 funding-file accounting on the same 204 days: 612 eight-hour settlements per asset. Overlay funding PnL BASE -0.28793%, SEVERE -0.70900%, SUPERSEVERE -1.37660% of reference equity, using debit/credit multipliers 1/1, 1.25/.75, 1.75/.50. Combining **linear** price, funding and approximate overlay-change fees gives BASE +0.01014%, SEVERE -0.58593%, SUPERSEVERE -1.53353% equity. These are attribution diagnostics only: not the native simulator, not the complete portfolio, not compounded wealth or CAGR, and not an official promotion/rejection gate.

## Interpretation / blockers

The Phase266 overlay's BASE edge is approximately zero before native portfolio interactions, while severe/supersevere incremental components are negative. 2023 price-only fold was negative. This raises a strong **non-promotion warning**, not a claim of an official failed gate. Source annual CFTC snapshot point-in-time revision risk remains unresolved.

The prepared Phase266 workflow lacks the mandatory authenticated Clean-4 cache/rebuild step: the `phase243_clean4_canonical` directory is not tracked on the branch. It must restore/rebuild the source, validate its manifest, run two byte-identical native Phase266 evaluations, and enforce full causal/cost/fold/tail/concentration gates before any decision. Phase252 remains a partial candidate; no complete seven-slot champion promoted. V16/V99 untouched.
