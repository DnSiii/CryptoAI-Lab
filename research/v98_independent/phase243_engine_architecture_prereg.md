# V98 Independent Phase243 — engine architecture reset

Status: PREREGISTERED BEFORE SYSTEM PNL.

## Purpose

Phase243 converts the research program from serial isolated-alpha hunting into construction of the V98 complete engine defined by V98_NORTH_STAR.md.

This is a governance/architecture phase. It must not inspect V14/V15/V99 internals or use their performance to tune V98.

## Frozen architecture

The engine has seven slots:
- growth_core
- opportunity
- relative_value
- stress_recovery
- regime_router
- dynamic_allocator
- risk_governor

No slot is allowed to be filled by a previously REJECTED_NO_RESCUE / REJECT_FAMILY_NO_RESCUE experiment.

Historical V98 phases are evidence inventory:
- rejected => negative evidence only;
- data-only => data capability only;
- pass/promoted/frozen => eligible for further marginal-contribution review;
- unevaluated/preregistered => research backlog, not a component.

## Development sequence

A. Build a machine-readable inventory of all V98 phases and decisions.
B. Identify empty architecture slots and the strongest V98-only admissible evidence for each.
C. Develop new module candidates where a slot has no admissible component.
D. Freeze a first complete V98 engine specification before system-level PnL.
E. Evaluate the complete engine on chronological training folds with realistic costs/funding and all existing V98 diagnostics.
F. Optimize only through preregistered architectural hypotheses, never post-result rescue or massive grids.
G. Separate validation and untouched holdout remain locked until a complete frozen engine passes training.

## System-level selection philosophy

Do not require every individual sleeve to be a perfect standalone strategy. A sleeve may be useful if it has a preregistered positive marginal contribution to the frozen engine across folds/stresses without creating pathological tails/concentration.

Conversely, a high standalone return does not qualify a sleeve if its marginal contribution is redundant, unstable or dominated by one tail event.

The correct object of optimization is the complete V98 portfolio.

## Anti-overfit

- V98-only inputs for design.
- No external-engine parameter copying.
- No opened holdout reuse.
- No rejected-family resurrection.
- Small hypothesis-driven searches.
- Deterministic reruns.
- Full accounting for turnover, funding and execution lag.
- Explicit documentation of every architecture change before PnL inspection.

## Completion criterion for Phase243

Phase243 is complete when:
1. the historical V98 evidence inventory exists;
2. each architecture slot has a status: candidate / empty / needs-new-research;
3. a first complete system specification can be preregistered without consulting external engines.

No claim of V98 superiority is permitted during Phase243.
