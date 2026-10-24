# V99 I1 — native inverse-coin settlement invalidates USD-equivalent collateral assumption (2026-10-24 13:46 BRT)

**DECISION: ACCOUNTING BLOCK / DATA_ONLY/HOLD / NO PROMOTION.** This is a concrete, source-documentation-based accounting risk discovered while shortening the path to a full economic engine. It is **not** a backtest, alpha result, historical fill, native margin certificate, or paper PnL. The I1 implied-minus-realized variance screen remains an information-only observation.

## Actual repair and remote verification

- Implemented `inverse_coin_expiry_diagnostic()` in `research/tools/v99_r106_i1_defined_risk_options_ledger.py`. It keeps coin premiums in coin, converts a modeled USD intrinsic payoff to coin using the expiry **delivery index**, and reports the discrepancy against the earlier fixed-USD `expiry_nav()`. The existing USD-equivalent model remains explicitly illustrative, not native.
- The independent Decimal oracle reconstructs coin obligations and balances without reusing the diagnostic calculation, tests three settlement states, and rejects invalid delivery indexes. [GitHub Actions 40113052159](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40113052159) **SUCCESS**, **81 synthetic checks**. This is a genuine identified currency/collateral flaw; CI success does not make the options engine economically valid.
- `expiry_nav()` and `liquidation_nav()` now explicitly label themselves modeled and not native margin certified, and forbid promotion/orders in their output. The diagnostic does not silently change prior frozen models, paper or original results.

## Reproducible illustrative counterexample (NOT a historical trade)

Synthetic 2022-06-01 BTC 20,000/19,000 short-put vertical, 5 contracts, modeled initial capital $100,000 fully converted to 5 BTC at entry (ignoring FX conversion cost), initial BTC index $20,000, supersevere modeled fee/slippage 0.48% per leg. Net modeled entry premium = **$1,540 = 0.077 BTC**. At an illustrative expiry **delivery index $500**, the maximum intrinsic USD obligation is $5,000, but **coin obligation = 10 BTC**. Remaining modeled coin balance = **5.077 - 10 = -4.923 BTC**; the fixed-USD illustrative ledger would still show **$96,540 positive NAV**. The coin-account counterfactual would be insolvent *without earlier margin liquidation*. This is not a realizable negative account NAV or proof of an exchange liquidation; it proves that **USD-defined risk does not guarantee a solvent coin-collateral account**. Even at delivery index $18,000 the coin-valued USD account differs from the fixed-USD ledger by $10,154 in this example because coin cash has directional exposure.

The actual Deribit inverse option contract pays intrinsic USD value **divided by the delivery index in BTC/ETH** and premiums/margin are in coin, as described in the [Deribit inverse options specification](https://support.deribit.com/hc/en-us/articles/31424939096093-Inverse-Options). The current 2026 documentation must **not** be treated as a historically certified 2021-23 fee-tier or margin schedule. Actual expiry uses the venue's delivery index, not an OKX hourly open.

## Remaining exact path to an economically valid engine

1. Obtain licensed **original BTC+ETH Deribit executable option bid/ask, sizes, venue and arrival timestamps** throughout the 2021-12-09..2023-09-30 TRAIN, with expiry/strike/instrument, missingness manifest and legally usable provenance. Existing source has **0/188** required Monday BTC/ETH two-strike asset-week observations; authenticated archive key absent, public full downloads returned 403.
2. Obtain historically applicable **coin margin and liquidation**, expiry TWAP and **delivery-fee**, historical account-specific fee tier, and size-aware execution/fill assumptions. Coin-conversion and any delta hedge need explicit real cost/funding treatment. Hypothetical historical fills must be simulated, not misrepresented as real.
3. Rebuild one preregistered complete I1 engine with **coin and USD cash/inventory separated**, 5 fixed chronological TRAIN folds, two severe cost paths, 3x2 regimes, concentration, drawdown and benchmark gates, independent full reexecution; reject on failure. No [2023-10-01,2024-01-18) validation until new TRAIN pass and formal freeze; final holdout >=2024-01-18 remains sealed.

No orders. V16 Frozen, V99 Frozen, legacy champion, paper/results and public research status remain unchanged. **NO PROMOTION.**
