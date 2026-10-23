# V98 Independent Phase1203 — AD 180-cell independent rejection audit (2026-10-23)

## Immutable evidence and preregistered decision
Phase1202's already committed test explicitly expects **90 benign passes and 90 crisis failures**, with the AD_full / $10k / base / carried-before-fill crisis first failure `AD1202_T877_AD1196_UNEXECUTABLE_CARRIED_INVENTORY`. Phase1202 itself must not be changed or made to pass by modifying risk constants, quote capacity, shock size, thresholds, exposure, target interpolation or path ordering. Phase1200's earlier 90/90 crisis passes used **fixed synthetic risk inputs** and cannot override Phase1202's actual t-1 rolling causal risk gate.

Re-run the original Phase1202 180-cell test and `run()` on **ubuntu-22.04 and ubuntu-24.04**, pinned Python 3.11 / numpy 1.26.4 / pandas 2.2.3. Preserve all 180 cell receipts and exact first failures as GitHub Actions artifacts. Require 90/90 benign pass, 90/90 crisis fail, all five paths and three capital modes and three fee modes and two funding timings present, no historical PnL, no validation, no external benchmarks. Require exact string equality for failure reasons and <=1e-8 tolerance for benign numeric receipts across OS.

**Scientific decision:** a confirmed crisis failure rejects AD_full as a candidate under its own Phase1202 structural preregistration. Do not attempt a cosmetic governor/parameter repair. A dual-runner mismatch blocks any independent attestation but does not erase the observed local rejection. No historical AD system PnL may run while structural gate fails.

Next work is a genuinely distinct seven-slot architecture with independently preregistered economic thesis and fresh causal code, not a revision of AD or a copy of any rejected engine. V16, V99 and external benchmarks remain unopened and untouched.
