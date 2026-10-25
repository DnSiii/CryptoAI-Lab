# V99 I1 — prevent forged modeled NAV and opening-fee identity (2026-10-25 15:51 BRT)

**SOURCE_ONLY/HOLD — NO PROMOTION.** This repairs an actual accounting-integrity weakness in the reusable I1 options ledger. It does not create a historical trading strategy, native margin model, certified historical fee tier, original fills or economic ROI.

## What was defective

The immutable `Spread` dataclass could be manually constructed or modified with a quantity above the 5% preregistered width budget, a collateral reserve inconsistent with strike width, or an opening cash balance inconsistent with the premium. Downstream expiry/mark/coin replays trusted those fields without revalidating the opening self-financing identity. The native-coin replay also bound the net premium to the opening quotes but did not independently bind `entry_cost_usd` to the two modeled per-leg friction charges. These omissions could silently produce fabricated **modeled** NAV from an invalid position object.

## Actual implementation and remote verification

- Commit [10388fb5](https://github.com/DnSiii/CryptoAI-Lab/commit/10388fb5c392f7b596f7830a0b70933029a41df2): all four downstream NAV/replay paths now invoke a fail-closed spread invariant check: valid asset/scenario and Monday TRAIN date/tenor; finite positive quantity, capital and credit; strike-width collateral identity; <=5% capital risk; exact initial+credit cash identity; sufficient modeled collateral. Original-quote coin replay additionally binds entry friction to the actual modeled scenario.
- Commit [a44ac36e](https://github.com/DnSiii/CryptoAI-Lab/commit/a44ac36eaa4b5ceafdd05ec76c91a21c8eb60a6f): independent Decimal oracle now rejects eight hostile spread mutations across four downstream paths and a separate positive-but-forged opening fee.
- [GitHub Actions 40223199936](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40223199936) **SUCCESS** on final head. Job logs: **128** synthetic modeled-ledger checks (including 33 new adversarial assertions) and **28** independent inverse-coin replay cases. This is software-accounting verification, **not** a 2021–2023 economic TRAIN run, and not a source or fee attestation.

## Still on the critical path

- The authenticated archive probe [Actions 40218547903](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40218547903) confirmed that GitHub secret `TARDIS_API_KEY` is absent. **0/182** certified complete historical BTC/ETH entry-through-exit option lifecycles; no legal entitlement or original full 2021-12..2023-09 BBO+size/two-clock/gap tape is present. A subscription must explicitly include 2021 data; do not purchase on assumption.
- The ledger still uses modeled severe/supersevere friction, USD-equivalent width reserves, and explicitly hypothetical coin settlement. Historical native contract-lot increments, dated account fee tier and delivery fees, coin margin/liquidation and full exit liquidity are **not** authenticated. These cannot be inferred from a passing oracle.
- Next: obtain independently attributable full 21–45d BTC+ETH source slice and dated terms, then connect the native self-financing portfolio to original fills/marks and independently replay five chronological TRAIN folds, six regimes, severe/supersevere, drawdown, tails and benchmarks. Validation [2023-10-01,2024-01-18) and final holdout >=2024-01-18 remain sealed until a new candidate passes and freezes.

No Frozen V16/V99, paper/results, legacy champion, dashboard promotion or orders were modified. **NO PROMOTION.**
