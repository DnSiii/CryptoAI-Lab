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
