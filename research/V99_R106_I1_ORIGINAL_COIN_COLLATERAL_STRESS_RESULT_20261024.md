# V99 I1 — original Deribit TRAIN native-coin collateral stress: historical risk finding (2026-10-24, 19:51 BRT)

**Decision: MODEL RISK CONFIRMED; DATA_ONLY/HOLD — NO PROMOTION.** This is an actual original-underlying historical stress with hypothetical strike levels, **not** a historical option trading return, account insolvency, margin-call history, or proof of a profitable engine.

## Precommitted protocol and actual original-source run

- Ex-ante rule committed at `1ce5de2230b3689ea840bcc65ce8765d5b1f6888`, **before executing this stress**: `research/V99_R106_I1_ORIGINAL_COIN_COLLATERAL_STRESS_PREREG_20261024.md`.
- Original first-party Deribit `public/get_delivery_prices` BTC/ETH daily TRAIN-only artifact from Actions **40117855925**, already independently audited across 36 API pages, was recovered by CI. Both assets: **661 consecutive calendar days** [2021-12-09,2023-10-01), no validation/holdout data.
- Ex-ante 91 Monday 00:00 UTC decisions per asset. Only prior Sunday 08:00 index known at decision is used as entry spot proxy; Monday 08:00 **21 days later** is the hypothetical settlement index. Synthetic short put at 95% of entry index, synthetic long put at 90%, normalized 5%-of-entry-USD strike-width exposure; **zero premiums and zero fees** intentionally isolate native coin settlement risk.
- GitHub Actions **40140255429**, job **121010308033**, completed **SUCCESS** on 2026-10-24 22:50 UTC. The independent implementation recomputed all **182** source-bound observations using a separate piecewise payoff identity. Mutation of original index bytes and fabricated result rows were both rejected. Artifact **12578826171** holds the complete result.
- Branch compare from the previous entry-book cycle confirms the stress added its own preregistration, source calculator, independent oracle and workflow. No Frozen V16/V99, paper/results, legacy champion, public dashboard, orders or sealed partitions changed.

## Historical *underlying-index stress*, not trading ROI

| Metric | BTC | ETH |
|---|---:|---:|
| Eligible synthetic 21-day scenarios | 91 | 91 |
| 5%-coin-reserve breaches | **25/91** | **27/91** |
| Maximum inverse-coin obligation / 5%-coin reserve | **1.4543841910×** | **1.6638525976×** |
| Breaches by chronological fold 1–5 | **8, 10, 4, 0, 3** | **9, 10, 4, 1, 3** |

**Interpretation:** A vertical put spread's USD intrinsic is bounded by strike width, but its inverse BTC/ETH settlement obligation divides that USD amount by the settlement index. Consequently, earmarking 5% of an initial *coin* wallet from a 5%-of-USD strike-width assumption is **not** a guaranteed native-coin collateral bound. Actual original BTC/ETH index paths breached that illustrative coin reserve in multiple TRAIN windows. These are NOT real listed strikes, trades, fill prices, fee/margin calculations or liquidations. Do not label a 25/91 or 27/91 count as historical trading losses.

## Concrete path to a scientifically legitimate integrated engine

1. **Do not use the prior USD-equivalent put-spread risk fraction as native coin margin certification.** A live-equivalent simulator must model historical as-of Deribit margin/maintenance and forced liquidation, native contract size, collateral denomination and conversion/hedge policy before calculating economic risk. No native exchange liquidation history has been reconstructed for these hypothetical positions.
2. **Actual executable BTC+ETH option bid/ask+size remains 0/182 maturity-eligible asset-week pairs** from the existing partial Tardis source. The full original 2021–2023 entry **and holding-period** quote archive with exchange/local arrival timestamps and gap manifest requires an authorized entitlement. The authenticated `TARDIS_API_KEY` is absent in the archived probe. Amberdata is a potential alternative only after verified historical bid/ask, size, arrival-time and contract coverage; no purchase authorized.
3. With source evidence, execute **one** preregistered, complete, self-financing native-coin engine across five original chronological TRAIN folds, 3×2 regimes, severe/supersevere scenarios, independent trade/account replay, risk/tail/DD and benchmark gates. Freeze only if the full TRAIN passes. Validation [2023-10-01,2024-01-18) and final holdout >=2024-01-18 remain sealed.

**NO PROMOTION. No historical options ROI, no paper PnL, no live orders.** A successful CI here validates original-index stress accounting only.
