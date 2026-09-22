# V98 Independent — gross-guard semantics audit

The shared `exact_fast` simulator was audited after recent reports showed close-of-hour `max_gross` above the nominal 0.75 target.

Finding: this is expected causal drift, not target leverage. At every trade event the simulator clips requested target gross to `gross_guard_cap`. It then allows intrahour asset returns to change portfolio weights; the report field derived from `positions` is close-of-hour gross and can therefore exceed the cap until the next open. If the prior close gross exceeds the cap, a causal reduction is scheduled at the next hourly open. The engine intentionally does not claim intrabar cap enforcement from hourly OHLC data.

Policy for new V98 candidates: report both `max_open_gross` (execution/target risk) and `max_close_gross` (post-return drift). Add a mandatory invariant that `max_open_gross <= preregistered gross cap + tolerance`. Do not reinterpret old close-gross drift as hidden leverage.
