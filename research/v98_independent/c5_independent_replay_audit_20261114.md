# V98 C5 independent replay audit — 2026-11-14

Source: GitHub Actions run 43547805609, artifact 14095076910, SHA-256 ZIP digest b9c36e7ae72d47e3a51f3e2f208cc8855496d4a7dd3f2542bc7211b274801f88; branch research/v98-independent-zero, commit 69045b5fc9cbd574211f6a635a624eace476bba0.

**Scope:** training-only authenticated Clean-4, 27,048 source hours, 27,047 ledger rows per scenario; native funding; no holdout access reported. This is an independent arithmetic check of the archived ledgers, not an independent market-data or strategy-code reimplementation.

| Cost | Final equity (USD; initial 10,000) | Max DD | Growth marginal | Opportunity marginal | Relative-value marginal | Stress/recovery marginal |
|---|---:|---:|---:|---:|---:|---:|
| 1x | 15,202.71 | 15.72% | +1,619.94 | +1,069.20 | +1,567.76 | +111.25 |
| 2x | 14,095.59 | 16.10% | +1,079.81 | +447.58 | +1,528.08 | -59.56 |
| 4x | 13,440.93 | 17.91% | +2,080.64 | +658.18 | +2,197.93 | -73.15 |

**Arithmetic:** independently streamed all 81,141 ledger rows. Every row satisfies `pre_fill_equity = previous_equity * (1 + gross_return + funding_return)` and `equity = pre_fill_equity * (1 - cost_return)` exactly to float precision (maximum observed residual 0). Asset gross and funding sum to corresponding reported return within 3.5e-18 and 5.5e-20. Ledger turnover sums match summaries to floating precision. Each of 12 ablations satisfies `full_final_equity - without_final_equity = marginal_final_equity` to floating precision. Terminal summary equity is lower than last ledger equity by USD 1.1974 / 1.1102 / 1.0587 at 1x / 2x / 4x; consistent with previously documented terminal open-to-close marking, but source-code-level terminal calculation must be checked before final certification.

**Decision:** REJECT C5 for promotion under its preregistered robust positive-marginal criterion: Stress/Recovery has negative marginal contributions at 2x and 4x. Do not tune its threshold/sign/window after viewing this result. C3 and C4 remain rejected. No V98 champion established. This result does not demonstrate superiority to any external engine.

**Next critical work:** preregister a genuinely distinct seven-slot architecture hypothesis, execute authenticated chronological training and independent validation; confirm the terminal accounting implementation, evaluate regime/tail concentration and reproducibility before any promotion. Preserve untouched future holdout, XRP quarantine, Frozen, V99 and paper.
