# V99 R106 D1 — C160 independent full-TRAIN account + funding + risk chain (2026-10-23 BRT)

**Decision: DATA_ONLY/HOLD — NO PROMOTION.** No historical economic TRAIN, no ROI, no paper/results update, no real orders, no validation and no final holdout.

## Implemented and executed

- Integrated three previously separate independent source-only checks over the same two scenario journals: C150 cold-start + C149 Decimal accounting; C133/C132 complete 8h BTC/ETH funding calendar; C148 five-fold/six-regime risk scorecard.
- Added explicit cross-scenario starting-capital identity. Prior C148 used the severe scenario's initial NAV as both scenarios' baseline and did not independently compare the starting books; a forged but internally balanced supersevere initial balance could bias relative scorecards. C160 rejects it before risk calculation.
- Added a cross-check that C149 modeled funding-event totals agree with the independently checked C133 calendar.
- Added six synthetic negative/positive tests: complete 15,864h dual-scenario fixture; scenario-specific starting capital; missing funding fix with tampered aggregate proof; divergent scenario price; sealed validation hour; missing cost scenario.
- GitHub Actions **39956951028**, commit **82a4fdd416c2d304ca86d03c170cbb2e76282f36**, **SUCCESS**; **63/63 tests green** (57 prior + 6 C160). Full integration tests completed in 4.234 seconds. The permission guard separately passed.
- GitHub compare ad817fc...82a4fdd reports exactly three added files, zero modified/deleted files, so Frozen V16, Frozen V99, legacy champion, paper/results and prior results were not touched by C160.

## Precisely what is and is not proven

The deliberately flat fixture has **15,864 TRAIN hours per scenario**, **654 daily decision timestamps**, **five chronological folds [3,172, 3,173, 3,173, 3,173, 3,173]**, and **3,966 synthetic funding rows per scenario** (1,983 per asset). Both cost paths have zero trades, zero modeled alpha and 0/5 positive folds in the fixture. The fixture covers only the sideways/low-volatility regime: **1/6 regimes**. These are test inputs, **not a historical result or a rejection of the D1 strategy**.

C160 independently replays cash/positions/fees/funding and checks the schedule and risk, but the existing C148 dependency accepts a self-declared c146_full_feature_funding_proof count. **The C146 full feature/funding decision re-execution is not yet integrated remotely.** A green C160 test must NOT be described as complete causal decision verification.

Neither a fabricated 8-hour funding schedule nor source=OKX labels establish first-party provenance. Historical account-specific fee tier, native instrument specifications, actual settled funding, paired spot/perp hourly history and executable fills remain unverified for the complete TRAIN. **Historical ROI is not authorized.** No scientific promotion follows from synthetic or CI success.

## Next justified critical path

1. Integrate the remaining local C152 model hourly journal and C140–C147 feature/funding/re-execution modules additively, without changing preregistered D1 parameters; connect to C160 and native lot C151.
2. Establish independently anchored first-party historical OKX data/terms/fills for the exact TRAIN period. If evidence remains unavailable, retain DATA_ONLY/HOLD and continue source verification, not PnL claims.
3. Only after source gate, run one fixed D1 economic TRAIN in both severe/supersevere scenarios, verify independent portfolio accounting, five chronological folds, all six regimes, tail/DD and passive benchmark envelope. Freeze only if formal gates pass, before opening sealed validation [2023-10-01,2024-01-18); final holdout >=2024-01-18 remains unopened.

**C1/C2 and archived rejected alpha remain rejected; no parameter retune, no real orders, no paper publication, no ROI claim, NO PROMOTION.**
