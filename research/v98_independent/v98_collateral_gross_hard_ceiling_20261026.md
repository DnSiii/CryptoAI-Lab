# V98 Independent — hard stressed-collateral gross ceiling (2026-10-26)

**READ-ONLY ALGEBRAIC DIAGNOSIS; NOT STRATEGY PNL, APPROVAL, OR PERMISSION TO RELAX RISK.** No holdout or market dataset read. Derived from the existing V98 Independent `cg_buffered_governor.py::buffered_safe` and `v98_staged_exit_viability_governor_v2.py`. The governor is unchanged; all rejected architectures stay rejected.

For long-only books, the governor's minimum instantaneous adverse floor is 40% (`down >= .40`); an additional 24 consecutive adverse continuation hours at 1%/h apply. The terminal price multiplier is at most

`m = (1 - .40) * (1 - .01)**24 = 0.4714068844843312`.

At entry, stressed terminal equity is `after - (1-m)*G - funding_reserve - exit_friction`, where `G = sum(abs(units*opening))` is authorized gross notional. The buffered entry rule requires terminal equity `>= .60 * after`. Since funding reserve and friction are nonnegative, a **necessary, not sufficient**, bound is

`G / after <= (1-.60) / (1-m) = 0.7567257087897942`.

This bound tightens for observed adverse gaps >40%, nonzero native funding reserve, nonzero exit friction, order-dependent reserve, maintenance, or other physical constraints. It does **not** imply 0.7567x is always reachable or that real exchange fills are available. It applies to long-only entries and assumes the specified floor; it does not establish a universal upper bound for short books or other collateral models.

| Desired long gross / NAV (illustrative) | Maximum authorization fraction from stressed collateral alone |
| ---: | ---: |
| 2.0x | <=37.8363% |
| 1.8x | <=42.0403% |
| 1.6x | <=47.2954% |

The observed HD 37.309% base authorized/requested at 2x-style desired exposure is therefore **consistent with a binding collateral-stress ceiling**, not proof of a broken API or missing order-book data. Previously reported 37–46% execution fractions must not be interpreted as available alpha that can be unlocked by multiplying the requested signal. The strict 60% stressed-NAV buffer and 40% adverse floor mean a long-only architecture must compete for ~0.76x feasible gross (or less), independent of its nominal 1.6–2.0x target. Cross-asset diversification does not loosen this particular simultaneous worst-case all-long floor.

**Critical-path implication:** New independent seven-slot portfolio hypotheses should maximize *net compounded growth inside the actually authorized exposure budget*, using genuine incremental marginal contribution, instead of multiplying nominal gross or cosmetically relaxing the safety buffer. Any proposal to change the risk model needs separately preregistered, authenticated adverse-gap, liquidation and market-impact evidence and new full physical validation; it cannot be applied retroactively to rejected runs. The currently pinned 1h OHLC/funding alone does not justify reducing the conservative stressed floor. Alternative: keep the current governor and develop new distinct alpha/sleeve allocation at feasible capacity.

HF was preregistered and implemented before this **read-only** diagnostic and is not changed by it. The HF official training run is independent of this note. No 2025/2026+, XRP, Phase083, V14/V15/V99 or Frozen/paper/live touched.
