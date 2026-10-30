# V98 Independent Phase241 — implementation/novelty audit

Audit performed before any Phase241 performance was observed.

## Historical-family check
Phase039 previously tested a 24h continuation construction: lagged price move multiplied by persistent relative quote-volume participation, daily rebalance, 720h volume reference, 720h beta neutralization, and gross 0.75. It failed all 2023/2024/2025 folds and stress gates.

Phase241 is related by data family but scientifically distinct in mechanism and execution: it tests cross-sectional dislocation/mean reversion, using robust abnormal log quote-volume (median/MAD), cross-sectional standardized interaction with the negative 24h return, hourly event formation, fixed k=1 extremes, H={4,8}, gross<=1, and no beta-neutralization/regime gate. Phase039 evidence must not be used to tune Phase241.

## Implementation audit
The preregistration is authoritative. r24(u) must be computed from the canonical close series, not open. Decision at open(t) consumes only av(t-1) and r24(t-1). Rolling median and rolling MAD are shifted one hour; the MAD floor is 1e-9 as preregistered. Quote volume must be canonical PIT quote volume.

The attempted evaluator draft was not committed and therefore produced no scientific result. Audit caught two draft/spec mismatches before execution: use of open instead of close for r24, and a 1e-8 MAD floor instead of the frozen 1e-9. Both are forbidden implementation drift and must be corrected before materialization.

## Frozen decision surface
Exactly four specs: vw={168,336}, k=1, H={4,8}. Costs 7/14/28 bp per L1 turnover; PIT funding; folds 2023/2024/2025; 2026+ forbidden. Required diagnostics and mechanical gate remain exactly as Phase241 preregistration/validation protocol.

Status: IMPLEMENTATION_AUDIT_PASS_WITH_REQUIRED_CORRECTIONS. No Phase241 performance observed; no rescue or parameter change authorized.
