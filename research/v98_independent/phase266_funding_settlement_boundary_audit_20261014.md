# V98 Phase266 — funding settlement boundary audit (2026-10-14)

The independent funding component from the previous cycle counted each ON interval as [entry 00:00, exit 00:00). However the V98 native exact_fast simulator settles funding **before** applying new targets at the same hourly open. For a daily 23:00 decision executed at next 00:00, the new overlay is not charged funding at its entry open, but is still charged at its exit open. Correct static-weight funding attribution must use (entry, exit], not [entry, exit).

Recomputed all four Clean-4 funding CSVs directly from the V98 branch; each interval contains 612 funding events per asset in either convention. Reproduced the old BASE total -0.287929625% exactly, then replaced the seven entry settlements with the seven exit settlements for each asset.

| Tier | Previous funding component | Boundary-corrected static-weight component | Difference |
|---|---:|---:|---:|
| BASE | -0.287930% | -0.285346% | +0.002583 percentage points |
| SEVERE | -0.709000% | -0.706037% | +0.002963 percentage points |
| SUPERSEVERE | -1.376598% | -1.372742% | +0.003856 percentage points |

The correction is small and **does not rescue the hypothesis**. These are fixed-weight additive funding components, not the complete native portfolio with position drift, fees and compounding. No source/sign/threshold/weight change was made. The native exact simulator must still be executed, including identical BASE/SEVERE/SUPERSEVERE comparator and all frozen gates. Phase252 remains partial; no complete champion. CFTC point-in-time archive revision provenance remains unresolved. V16/V99 and holdout untouched.
