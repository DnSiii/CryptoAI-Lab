# V98 Independent Phase259 — Network-Security Expansion decision

Status: **REJECT_NETWORK_SECURITY_EXPANSION_NO_RESCUE**.

Phase259 used only the passed Phase258 hashrate series and the frozen 30d-vs-prior30d rule. The first workflow failure was a synthetic-test horizon bug; the test-only fix changed no strategy parameter, signal, data or gate. The corrected rerun was deterministic and completed.

BASE:
- Phase252: +550.57%, CAGR 86.66%, PF 1.2169, DD -52.64%
- Phase259: +626.52%, CAGR 93.65%, PF 1.2084, DD -60.23%

SEVERE:
- Phase252 +493.66%
- Phase259 +551.70%

SUPERSEVERE:
- Phase252 +408.80%
- Phase259 +442.77%

Marginal calendar return versus Phase252:
- 2023: +46.53pp
- 2024: +21.95pp
- 2025: -10.37pp

The sleeve was active on 874 decisions / 79.74% of training hours.

Three frozen gates failed:
- BASE PF fell below Phase252;
- DD worsened by more than 5 percentage points;
- 2025 underperformed Phase252 by slightly more than the frozen 10pp tolerance.

Therefore the exact 30d-vs-prior30d hashrate-expansion / +0.25 gross rule is rejected. No window, sign, threshold, sleeve-size, risk filter or regime rescue is allowed.

Important retained evidence: network-security expansion increased aggregate and stress-tier wealth materially, but the exact implementation is too broad/risky and chronologically weak in 2025. This is evidence for the frontier, not authorization to retune Phase259.

Phase252 remains the frozen partial architecture. Validation/holdout remain locked. V14/V15/V99 were not used.
