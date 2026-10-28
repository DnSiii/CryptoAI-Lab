# V99 I1 — scenario-specific decision ledger preregistration (2026-10-28 08:5x BRT)

## Verified internal blocker
The existing 661-day native event replay binds one global 180-row decision ledger to both severe and supersevere scenarios. It requires exactly identical OPEN asset-weeks, although cost-dependent solvency/maintenance vetoes can legitimately produce different exposure paths. This is an incorrect structural constraint and prevents truthful scenario-specific risk accounting. A global self-declared CASH reason is not independent source evidence.

## Ex-ante change contract
1. Nonfixture journals MUST provide `scenario_decisions` with exactly `severe` and `supersevere`, each with exactly 180 fixed BTC/ETH Monday entries, matching the same original causal signal/fold/clock for each key. Legacy single `decisions` is allowed ONLY for explicitly synthetic fixtures; reject nonfixture legacy-only input.
2. Validate each scenario's own OPEN events against its own ledger; never infer identical positions from a different cost path. For positive signals, CASH may be `NO_ELIGIBLE_FIXED_VERTICAL` or `RISK_VETO` only, still explicitly unverified until independent source and risk replay. Reject OPEN without positive signal, missing/duplicate/shifted rows, unsupported reasons, mismatched event signals, cross-scenario signal tampering, and unaccounted OPEN.
3. Add `scenario_decisions_self_declared_not_certified: true` to output, retain ALL existing no-certification/no-promotion/no-holdout flags. No economic performance, source authentication or release gate is unlocked.
4. Test a controlled synthetic cost-path difference, adversarial cross-scenario signal mismatch and incomplete scenario ledgers. Run CI via the existing native-event workflow and poll its result.

## Boundaries
No changes to original 182 signals, C1 rejection, frozen, paper, legacy champion, validation or holdout. No orders. This is a necessary accounting correction, not a claim of an edge. Historical 661-day licensed original options quotes/size/arrival, native historical fees, inverse-coin margin/liquidation and settlement evidence remain unavailable; certified original lifecycles remain 0/180.
