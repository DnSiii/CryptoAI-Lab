# V98 Independent Phase140 — governance reconciliation

The branch contains two Phase140 preregistration artifacts. The stricter
`v98_independent_phase140_treasury_curve_pit_feasibility_prereg.md` was
committed before final economic authorization and governs the decision.

The earlier month-end audit remains valid positive evidence (36/36 sampled
vintages, 1,501 overlaps, zero mismatches) but its `PASS_PIT_SHORTCUT`
does not authorize Phase141.

The canonical Phase140 executor is now the existing single main path:
`scripts/v98_independent_phase140_t10y2y_pit_audit.py`. It performs the
full annual PIT feasibility gate required by the stricter preregistration:
every weekday observation date in 2023-2025, observation+1-day ALFRED
vintage, >=95% usable coverage in each year, no future/backfilled exposure,
and two independent full acquisitions with normalized hash equality.

The initial per-vintage implementation failed on the first transport request
before producing a scientific report. To avoid 1,566 fragile single HTTP
calls, the same vintages are now transported in ALFRED multi-vintage batches
of 12. This is a transport-only change; source, series, dates, availability
contract, coverage gate, double acquisition and isolation rules are unchanged.

Only `PASS_PIT_DATA_ONLY` from
`reports/v98_independent_phase140_t10y2y_full_pit_audit.json` authorizes a
separate Phase141 economic preregistration.
