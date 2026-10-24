# V99 — independent PIT options IV/index moneyness quality result (2026-10-24 BRT)

**DATA_ONLY/HOLD — NO PROMOTION.** This is not an economic trial or a model. The 1000-depth source gate passed 5/5 folds for unnormalized strike availability, but a more comparable near-ATM trade-IV quality screen does **not** yet support claiming stable four-group term/skew inputs.

- [Actions 40068150433](https://github.com/DnSiii/CryptoAI-Lab/actions/runs/40068150433) downloaded the **original archived 1000-depth receipts** from Actions 40067965880; no additional exchange downloads or later-date queries. It recomputed source SHA-256 and causal timestamps and independently checked all IV/index field counts. Source-quality artifact **12550266188**.
- **187,588 / 188,000** sampled option trade rows had simultaneously finite positive historical `index_price` and plausible positive `iv` under the explicit range gate. This is *field availability*, not yet an independent certification of whether each index value represents contemporaneous exchange observation rather than a later recalculation.
- Diagnostic: restrict trades to <=6h old, <=15% absolute log-strike/index moneyness and 7–45d or 46–120d expiry. Require >=2 distinct strikes per call/put in both maturity bands. This moneyness diagnostic was **not** part of the original preregistered 1000-depth source gate, so its 70% fold check is an engineering diagnostic, **not** a preregistered alpha rejection.

| Fold | BTC near-ATM four-group availability | ETH near-ATM four-group availability |
| --- | ---: | ---: |
| 1 | 14/19 | 14/19 |
| 2 | 12/19 | 11/19 |
| 3 | 15/19 | 8/19 |
| 4 | 16/18 | 12/18 |
| 5 | 17/19 | 14/19 |

At a *diagnostic* >=70% weekly availability for both assets, only folds **1 and 5** pass (2/5). No strategy returns were observed. The complete 24h chain is still truncated in 188/188 1000-depth samples, so a weak near-ATM sample does not prove an absent underlying option market. Do not call 5/5 **raw** information coverage a 5/5 stable, comparable **IV signal**.

**Next actual gate:** independently verify Deribit's historical trade `index_price` timestamp semantics and obtain an auditable, broader **strike/maturity-comparable** PIT IV surface (prefer instrument/expiry-specific first-party source selection over unbounded blind pagination). Only then preregister one economically rational integrated portfolio engine. Original native OKX fee tier, settled funding and executable spot/perp fills remain separate blockers to economic certification. Preserve all TRAIN/validation/holdout separation and Frozen/paper. No serial strategy tuning or ROI claims.

**NO PNL. NO PROMOTION. NO ORDERS. NO PAPER WRITES.**
