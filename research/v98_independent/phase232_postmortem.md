# V98 Independent Phase232 — post-mortem

Decision: **REJECT_FAMILY_NO_RESCUE**.

The decision-grade run completed successfully with training-only rebuild, `<2026-01-01` firewall, point-in-time funding, deterministic duplicate execution, cost monotonicity and independent validation. Validator reported zero survivors: every one of the eight frozen specs failed the annual gate in 2023, 2024 and 2025. Canonical validator SHA: `ba70119233d5d8fbaa25226b1bf39db7e20cf4fdba683759726fb04ffb102229`; deterministic payload SHA recorded by results: `5092a8e5a3e5a087d8379654b9c9e87c105c36a09945750cfff7874c8a5990d3`.

Failure mechanism is broad rather than a single-fold accident. For `beta_disp_lb168_k1_h4`, 2023 base returned -74.46%, PF 0.893, max drawdown -77.72%, payoff 0.927, positive days 48.22%, win rate 49.08%. Bear, bull and sideways regime returns were all negative (-11.11%, -42.68%, -49.87%). PnL concentration was high (max asset concentration 80.19%), with SOL the dominant negative contributor (-1.5135 simple-PnL contribution). Severe costs worsened return to -76.95% and DD to -79.81%, consistent with turnover drag rather than a hidden robust edge.

The validator establishes the stronger family-level fact: all 8 specs failed all 3 chronological folds, so there is no scientifically defensible rescue, sign flip, regime filter, asset exclusion or parameter refinement. Trade-event tails remain diagnostic only because overlapping sleeves make portfolio accounting authoritative.

Phase233 was preregistered before Phase232 results existed and is therefore eligible as the next distinct hypothesis. Phase232 evidence may only justify moving on; it must not alter the frozen Phase233 grid or gates. Holdout 2026+ remains unopened. V16/V99/paper state are outside scope and untouched.
