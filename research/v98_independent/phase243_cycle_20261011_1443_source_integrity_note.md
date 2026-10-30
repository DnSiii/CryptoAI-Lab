# V98 Phase243 source integrity — 2026-10-11

This is a data-integrity audit only. No model selection or holdout access.

- Applied the source capture fix in commit ea4a8d7899faa46881b72789cf735034fa46c192. The corrected Git blob is 6abeff2fcf2fe81ceba9f947333d350ee17a02a9.
- BNB canonical training data contains 1,800 literal zero rates among 3,288 settlements. July 2024 has 84 zero rates among 93 events, with a 77-event continuous zero sequence.
- Exact conditional uniform-arrangement calculation: P(max July zero run >= 77 | 84 zeros, 93 events) = 160/1345224943. This is a retrospective mathematical null, not an exchange-behavior model and not evidence of authenticity.
- The frozen XRP comparison contract requires checking all 24 monthly, daily, and minute-aggregated hours. A local checker was corrected to enforce this; the independent daily source files are still missing.
- Local tests: 107 passed in each of four deterministic configurations (428 executions). No historical strategy test was run.

Phase240 remains rejected. Phase243 is blocked pending independent original-source reconciliation. No champion has been promoted.