# V98 Independent Phase1014 — cross-CPU float64 forensic conclusion (SOURCE ONLY)

Authenticated sources: Phase1010 run 39924141989, AMD EPYC 9V74 (artifact `v98-independent-phase1010-o-target-a`), and Phase1014 run 39925018026, AMD EPYC 7763 (artifact `v98-independent-phase1014-target-a`). Both independently verified the exact same four canonical Clean-4 CSV SHA256 pins and unchanged Phase1006 O source Git blob. The Phase1014 within-run OS22/OS24 comparison alone was same-CPU (both EPYC 7763), so it was **not** misrepresented as a heterogeneous comparison. The archived raw float64 arrays from the two *different* CPU families were then compared offline byte-for-byte/elementwise, with no economic returns read.

| Frozen O path | Max absolute float64 target difference | Different exact float64 elements | Differences >1e-12 | Differences >1e-10 | Active-mask changes |
| --- | ---: | ---: | ---: | ---: | ---: |
| O_core_only | 1.6653692314072543e-13 | 51,031 | 0 | 0 | 0 |
| O_full | 1.2811973704174306e-13 | 51,438 | 0 | 0 | 0 |
| O_minus_opportunity | 1.2811973704174306e-13 | 51,462 | 0 | 0 | 0 |
| O_minus_relative_value | 1.6653692314072543e-13 | 51,294 | 0 | 0 | 0 |
| O_minus_recovery | 1.2811973704174306e-13 | 51,031 | 0 | 0 | 0 |

**Classification:** `CPU_DEPENDENT_SUB_PICOUNIT_FLOAT_ROUNDING` is consistent with the observations. All five 12-significant-digit target CSV hashes differed between these CPUs, but all five eight-significant-digit hashes were equal. The max absolute raw target difference was **1.6653692314072543e-13**, with **zero >1e-12** and **zero active-mask changes**. This explains why Phase1008 exact 12g pin checks sometimes failed despite identical vendor-pinned data and O source code. It does NOT prove bitwise execution determinism; the Phase1008 raw hash freeze remains quarantined.

**Decision:** no economic O training or benchmark permitted from raw CPU-sensitive float64 targets. Continue with preregistered Phase1015 eight-significant-digit-minus-one-quantum deterministic *non-increasing* execution transport and independent cross-runner verification. This is a numerical transport fix before any economic PnL, not a rescue of rejected N or a parameter/return adjustment. V16/V99 and 2025+ validation/holdout untouched.
