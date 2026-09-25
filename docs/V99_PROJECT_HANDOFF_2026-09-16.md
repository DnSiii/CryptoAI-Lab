# V99 Project Handoff — 2026-09-16

Durable project snapshot created before deletion of the old V99 chat.

## Repository / branch
- Repository: `DnSiii/CryptoAI-Lab`
- Active research branch: `research/v99-r106-native-all-regime-engine`
- Research-only development must remain isolated from Frozen assets.

## Hard safety constraints
- NEVER modify V16 Frozen.
- NEVER overwrite V99 Frozen.
- V99 paper remains PAPER_ONLY / UNVALIDATED / no real orders.
- New research must preserve causal t-1 features, chronological train selection, untouched holdout, temporal folds, severe and supersevere costs, regime matrix, benchmark envelope and anti-overfit discipline.
- Do not promote cosmetic improvements or versions created just to show progress.

## Current research champion
R106 F7/F9 Core remains the research champion. F9 selected no additional cells, so F9 Core == F7.

Exact snapshot used by recent phases:
- Historical ROI: +43,522.48%
- Terminal multiple: 436.2248x
- Max drawdown: -32.1849%
- Worst day: -11.5498%
- Trade win rate: 29.5969%
- Profit Factor: 1.72310
- Payoff: 4.09879
- Positive days: 47.9184%
- Max losing streak: 28

Untouched holdout:
- ROI: +1,118.02%
- Max drawdown: -29.2544%
- Worst day: -8.2163%
- Trade win rate: 29.5711%
- Profit Factor: 1.78591
- Positive days: 48.5597%
- Payoff: 4.25346
- Max losing streak: 25

Older snapshots showing approximately +45,928% history / +1,185% holdout were from a slightly different snapshot/window, not a different strategy motor.

## Important rejected research after F7/F9
- Phase 14: BULL+LOW_VOL directional structural gate rejected; side behavior unstable across folds/holdout.
- Phase 15: Shadow Alpha Health Controller rejected; no train-stable rule.
- Old R81 gross drawdown brake rejected; small risk improvement but weaker wealth/PF.
- Phase 16: SIDEWAYS+HIGH_VOL mean-reversion sleeves all lost money in train.
- F9 SHV impulse transplant rejected as temporally unstable.
- Phase 17: BULL+LOW_VOL leadership sleeves aggregate-positive but fold/tail unstable.
- Phase 18: causal BLV market-structure router rejected; no state+sleeve pair passed train gates.
- Phase 19: BROAD_ADVANCE short-veto rejected; shorts were weak, but longs were even worse.
- Phase 20: BROAD_ADVANCE long taxonomy diagnostic found no robust healthy long subset.
- Phase 21: full BROAD_ADVANCE neutralization rejected. Historical ROI fell from +43,522.48% to +30,489.13%; holdout from +1,118.02% to +744.93%; DD improved but PF/return/stress degraded. No post-hoc partial scaling allowed.
- Phase 22: SIDEWAYS+HIGH_VOL long/short attribution showed nonstationary side behavior; no directional veto justified.

## Current active phase at handoff
Phase 23 — BEAR+LOW_VOL F7 long-vs-short attribution.

Files:
- Script: `scripts/run_v99_r106_phase23_blv_bear_lowvol_side_attribution.py`
- Workflow: `.github/workflows/v99-r106-phase23-bear-lowvol-side-attribution.yml`
- Target report: `reports/candidate_v99_r106_phase23_bear_lowvol_side_attribution.json`

Known run at handoff:
- Workflow run ID: `35132452335`
- Job ID: `104916497543`
- Last known state: in progress, exact replay step running without infrastructure errors.

Decision rule:
- Only create the next candidate if one side is stably harmful in train and the opposite side is stably healthy, with aggregate + robust-tail evidence and >=3 supporting temporal folds.
- Holdout is descriptive only for selection.
- If no stable asymmetry exists, do NOT continue endless regime-by-regime side microengineering. Change research direction.

## Strategic conclusion from recent research
Repeated hand-engineered price/regime microcontrols have failed to transfer robustly. If Phase 23 also fails, likely end the price-derived regime-filter microengineering campaign instead of manufacturing F24/F25.

Preferred next research direction if P23 fails:
1. Inspect older branches/reports first to avoid recycling prior ideas, especially R99-R104 and older drawdown branches.
2. Consider research-landscape / alpha-source decomposition across existing engines, searching for independent return sources rather than more hand filters.
3. Inspect repository/data availability for truly orthogonal features such as funding, basis, open interest, liquidations, volume/flow. Do not invent unavailable feeds.
4. Consider episodic drawdown/path analysis only after checking old drawdown research.
5. If adaptive additions keep failing, accept F7/F9 as the current robustness frontier rather than forcing a new version.

## Paper trading
Five V99 paper variants exist:
- `r98`
- `f1`
- `f3`
- `f7`
- `f12`

All are PAPER_ONLY, same fixed boundary, no recalibration.
Paper boundary: `2026-09-16T13:00:00+00:00` (10:00 São Paulo).

## Dashboard
Public dashboard:
`https://dnsiii.github.io/CryptoAI-Lab/dashboard/`

Relevant dashboard files:
- `dashboard/v99_research.js`
- `dashboard/v99_categorical.js`
- `dashboard/layout_fix.js`
- `.github/workflows/deploy-dashboard-gh-pages.yml`

Dashboard status:
- Full V99 Backtest/Paper panels are implemented.
- Daily charts use equal-spaced categorical calendar-day X axis in São Paulo.
- Only the explicit 24h paper chart remains hourly.
- The categorical daily rendering fix was confirmed as correct by the user.

## Communication / automation expectations
- User wants concise PT-BR updates, metric/status first.
- Avoid generic statements such as “evoluímos”.
- Hourly automation should report only: what was tested, main result, reject/promote status, next step.
- Do not ask for permission phase-by-phase unless a real blocker requires user action.
- Main objective remains: a materially superior, robust V99 — higher real return because the engine sees better opportunity, not because of hidden leverage, cherry-picking or loss suppression.

## Durable principle
Rejected phases are rejected hypotheses, not new robot versions. Prefer fewer versions and stronger evidence.


---

# Research update — 2026-09-25

This section supersedes the old "Phase 23 active" status above. Historical notes remain preserved for auditability.

## Current champion

R106 F7/F9 Core remains the research champion. No later phase has earned promotion. V16 Frozen and V99 Frozen remain untouched.

## Frontier conclusion after Phase135

The research campaign has now produced strong negative evidence against repeated transformations of the same information families.

Recent positioning/crowding Phases105–109 all failed train with 0/4 healthy folds. Raw aggTrades/taker/trade-structure Phases120–124 also failed decisively with 0/4 healthy folds after independent availability/integrity audits had already passed. Price/volatility/residual Phases125–135 likewise failed to establish a transferable train edge.

Phase135 return/volume coupling was the final canonical-OHLCV continuation test in this campaign:
- status: TRAIN_ALPHA_REJECT;
- train ROI: -42.78%;
- PF: 0.784;
- 0/4 healthy folds;
- no holdout use;
- no rescue/sign flip allowed.

Durable frontier controls:
- `research/v99_r106_frontier_audit_through_phase134_20260925.md`
- `research/v99_r106_source_orthogonality_inventory_after_phase135_20260925.md`

Research policy is now source-level: do not continue a numerical phase conveyor using cosmetic OHLCV, funding, positioning, OI, taker, or trade-structure transforms. A new alpha must first prove genuinely new point-in-time information.

## New orthogonal source — OKX cross-venue data

Phase136 opened a genuinely new second-venue information source using the official OKX public 1H USDT perpetual history endpoint.

Frozen instruments:
- BTC-USDT-SWAP
- ETH-USDT-SWAP
- SOL-USDT-SWAP
- XRP-USDT-SWAP
- DOGE-USDT-SWAP

Frozen train window: 2021-12-01 00:00 UTC through 2024-01-17 23:00 UTC.

Phase136 DATA_ONLY result:
- PASS_DATA_ONLY;
- 18,672/18,672 hourly rows for each of all five instruments;
- 100% coverage for each;
- zero non-hourly gaps;
- zero unfinished candles;
- all train-fold anchors present;
- two independent acquisitions produced identical normalized full-row SHA-256 for every instrument;
- no return relation, alpha, PnL or holdout was inspected.

Report:
`reports/candidate_v99_r106_phase136_okx_crossvenue_data_audit.json`

## Current active economic test — Phase137

Phase137 is the first economic test authorized from the new OKX source.

Frozen hypothesis:
- spread = log(Binance USD-M close / OKX USDT-SWAP close);
- 168h rolling median baseline;
- 168h MAD scale;
- score = -tanh(standardized dislocation), i.e. mean reversion;
- cross-sectional demeaning across the frozen five assets to remove common venue premium;
- complete score shifted t-1;
- L1 normalization;
- alpha gross 0.20;
- severe-cost train selection;
- no grid, no sign flip, no symbol substitution.

The first Phase137 workflow aborted pre-PnL because the runner assumed complete Binance rows. Existing canonical evidence showed BTC/ETH/DOGE complete while SOL/XRP each have 120 missing canonical hours (>99% coverage overall). No Phase137 PnL/result was produced.

Missing-data handling was then frozen before rerun:
- never fill/interpolate Binance gaps;
- require >=98% Binance coverage per frozen symbol;
- compute only on naturally available same-hour pairs;
- require >=4 contemporaneously valid cross-sectional scores or set alpha to zero;
- no symbol substitution.

Incident record:
`research/v99_r106_phase137_pre_pnl_binance_alignment_incident_20260925.md`

Latest known Phase137 rerun at this handoff update:
- workflow run: 36141870417;
- status: in progress;
- no result recorded yet.

## Immediate decision rule

If Phase137 fails the train stability gate, reject it permanently. Do not flip the sign to continuation and do not rescue the 168h window.

If Phase137 passes, freeze the exact specification and proceed through supersevere costs, regimes, tails/concentration, benchmark envelope and reproducibility before any untouched-holdout evaluation.
