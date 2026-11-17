# V98 Independent C9 — seven-slot economic gate (2026-11-17)

Scope: research/v98-independent-zero; authenticated Clean-4 training only. No 2026+, holdout, V14/V15/V99 benchmarking, or paper promotion.

Evidence: GitHub Actions runs 44152023576 and 44152070168, both completed successfully, with archived JSON artifacts 14359279469 and 14359638473. Both jobs report price manifest SHA256 01e7bdeb8bcaf34ee898e322cf20f4479c0e25a9066b40f8cd2446286259f8a8 and funding manifest SHA256 f33094dfc065aa862a529d46f36e15f8a418ab085780214a0423488d2ff49622.

C9 baseline final equity (initial USD 10,000): 1x USD 22,677.66; 2x USD 17,659.42; 4x USD 13,717.53. Baseline maximum drawdowns 13.54%, 13.98%, 18.05%. Training replay, not independent validation.

All four sleeves have positive leave-one-out marginal equity at all costs, but Growth Core at 4x adds only USD 23.32 and Opportunity only USD 53.82. These are fragile and not robust proof of superiority.

Seven-slot overlay diagnostics (baseline minus disabled-module equity; USD):

| Module | 1x | 2x | 4x |
|---|---:|---:|---:|
| Regime Router | +3,707.59 | +1,146.00 | **-600.27** |
| Dynamic Allocator caps | +1,275.26 | +39.40 | **-108.12** |
| Risk Governor | -2,706.83 | -5,303.03 | -5,070.98 |

The governor's negative equity contribution is NOT grounds for removal: it is a survival constraint, and disabling it increases max drawdown at 1x (13.54% to 14.54%) and 2x (13.98% to 15.42%). Counterfactuals are diagnostics, not deployable alternatives. In the observed counterfactual, gross exposure still peaks at 0.75; this does not establish that the governor is dispensable.

**Decision: C9 FAILS the robust seven-slot positive marginal contribution gate under supersevere 4x costs (Router and Allocator). Do not promote or freeze as champion.** This is not a license to retune sign, thresholds, windows, caps or leverage on these results. C9 stays an immutable rejected experimental reference; pursue a genuinely distinct preregistered complete seven-slot architecture. Keep historical chronological validation separate from training and untouched future holdout; no external benchmarks until internal candidate freeze and independent validation.

Next critical-path work: preregister a distinct architecture, run its complete native-source economic replay and seven-slot ablations at 1x/2x/4x, then chronological out-of-sample validation with independent implementation/reconciliation and predeclared economic/risk gates. Do not infer deployment readiness from successful GitHub job completion.
