# V98 Independent Phase138 — frozen decision audit

Status: **REJECT_NO_RESCUE**.

Phase138 completed successfully at the workflow/runtime level and produced reproducible training-only evidence. The hypothesis is rejected because the frozen gross-exposure gate failed.

## Evidence

- Aggregate training return: +84.37%; daily PF 1.272; max drawdown -22.37%.
- Folds: 2023 +35.12% / PF 1.543; 2024 +27.39% / PF 1.292; 2025 +6.89% / PF 1.085.
- Severe: +77.80%, PF 1.255. Supersevere: +67.11%, PF 1.227.
- Top-10 positive-day share 13.42%; largest positive asset contribution SOL 26.77%.
- Regime return-sum approximations were positive in bear, bull and sideways training regimes.
- Frozen gross cap failed: observed max open gross 0.5000014034568205 versus cap 0.50 with tolerance 1e-6.

## Decision discipline

The numerical magnitude does not authorize reinterpretation after observing results. No tolerance widening, arithmetic adjustment, alternate lookback, threshold, direction, regime filter, or rescue is permitted. Validation and final holdout remain unopened; V16, V99 and Phase083 selection evidence were not used.

This is an execution-contract failure rather than proof against the macro thesis, but promotion requires every frozen gate. Phase138 is permanently closed as REJECT_NO_RESCUE.
