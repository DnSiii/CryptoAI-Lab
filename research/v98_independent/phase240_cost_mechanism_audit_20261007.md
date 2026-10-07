# V98 Independent — Phase240 independent cost/mechanism audit (2026-10-07)

**Scope:** exclusively `research/v98-independent-zero`, existing Phase240 training-only results for calendar 2023/2024/2025. No V99, no Phase241 results, no 2026+ holdout. This audit does not change any frozen experiment, gate, or champion.

## Source and exact accounting method

Source: `research/v98_independent/phase240_results.json`, payload SHA256 `399e281185ddbc6783835686c05fa218313de74dd3d79f043a07d615ce67b49c`. For each of the 8 frozen specs x 3 folds = **24 base-cost cells**, let `net_additive = sum(asset_pnl_contribution.values())`, `cost_debit = 0.0007 * turnover_l1`, `pre_trade_cost_additive = net_additive + cost_debit`. This last quantity includes funding; it is NOT compounded portfolio return and must not be mislabeled as such.

The 7-to-14bp additive PnL decrement was independently checked against `(0.0014 - 0.0007) * turnover_l1` for all 24 cells; maximum absolute discrepancy was **1.78e-15** (floating-point rounding).

## Findings

- **15/24** cells were negative even before trade-cost debits; **9/24** were positive pre-trade-cost but still negative after costs.
- By year: **2023: 0/8** positive before costs; **2024: 4/8**; **2025: 5/8**. This indicates both lack of stable raw edge (especially 2023) and prohibitive implementation turnover.
- Base trade-cost debits ranged **3.2809 to 4.7172** units of additive portfolio PnL per annual cell (median **4.0025**); base additive net PnL ranged **-5.2136 to -3.1186**. These are sums of hourly portfolio return components, **not percentage account drawdowns**.
- Funding contributions ranged **-0.01346 to +0.00964**, much smaller in absolute magnitude than trade-cost debits; funding does not explain or rescue the losses.
- Compounded base returns ranged **-99.4805% to -95.7626%**, severe returns **-99.9953% to -99.8532%**, supersevere **approximately -100%**. Base PF ranged **0.5204–0.6900**; positive days **10.14%–20.49%**; base payoff **0.8736–0.9431** and win rate **36.58%–42.55%**.
- All **72 base regime subcases** (24 cells x bull/bear/sideways) had **negative compounded returns** and **PF below 1** (maximum PF **0.7154**). This is descriptive failure analysis, **not** a license to construct a regime rescue.
- Daily p01 tails were negative in all 24 cells. Base worst-day losses ranged from **-21.37% to -6.37%** across folds/specs. Maximum absolute asset PnL concentration ranged **20.97%–27.60%**, inconsistent with a failure confined to one asset.

## Scientific decision

Phase240 remains **REJECT_FAMILY_NO_RESCUE**. A few positive pre-cost cells are insufficient because the preregistered gates demand robust net results in *every* fold under base and severe costs. Do not lower costs, cherry-pick years, remove assets, flip signals or select regimes based on these observations.

Phase241 is a separately preregistered hypothesis and must be executed/validated without tuning from Phase240 outcomes. Its current status is **EXECUTION_READY_NO_PERFORMANCE_OBSERVED**. The blocked workflow write is an operational limitation; it is not performance evidence.
