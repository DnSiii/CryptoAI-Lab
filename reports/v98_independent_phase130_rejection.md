# V98 Independent — Phase130 decision

Decision: REJECT_NO_RESCUE.

Phase130 completed training-only evaluation before the workflow's post-run assertion failed. Scientific rejection is unambiguous: aggregate return -28.19%, daily PF 0.950, max drawdown -47.70%; 2023 -1.20%, 2024 +0.99%, 2025 -28.26%; severe -40.46%, supersevere -56.11%. Always-long context benchmark returned +59.81%.

Failure mechanism: the low/normal-RV permission state did not isolate positive expectancy. Approximate regime contribution was negative in bear (-0.154) and sideways (-0.200), only modestly positive in bull (+0.130). Asset contribution was not excessively concentrated (largest absolute share BTC 27.44%) and top-10 absolute-day share was only 8.81%, so failure is broad expectancy/path dependence rather than one asset or a handful of tails.

The reported max_open_gross 0.750046 exceeded the exact 0.75 guard by ~4.6e-5 and caused the workflow isolation assertion to fail. This does not rescue or invalidate the scientific rejection because multiple independent preregistered performance gates already failed materially. No threshold, lookback, lag, gross, asset, estimator, sign inversion, or state inversion will be tuned after observing these results.

Validation and final holdout remain untouched. V16 and V99 were not used. Phase083 was not used for selection. Champion remains none.
