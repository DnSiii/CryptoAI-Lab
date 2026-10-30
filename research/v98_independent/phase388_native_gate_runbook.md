# V98 Independent Phase388 — Native provenance-first runner (pre-execution)

Scope: only `research/v98-independent-zero`, `research/v98_independent/` and `.github/workflows/v98-independent-phase388-native-gate.yml`. This is a source/validation workflow, not a new alpha or parameter search. Existing immutable Phase243, Phase252, Phase305 and Phase379 preregistration remain unchanged. No 2026+ training, quarantined XRP, Phase083 holdout, V14/V15/V99 data or workflow changes.

1. Checkout exact V98 branch and rebuild authenticated Phase243 Clean-4 canonical hourly source. Never download 2026+ market data.
2. Verify immutable source/funding SHA and 8h event geometry; run Phase379 and Phase386 synthetic fail-closed tests.
3. Run Phase386 strict vendor receipt contract on the authenticated BNB funding CSV against the official Binance USD-M historical funding endpoint, with no alternate-provider fallback or post-result adjustment.
4. Only on exact independent provenance PASS, Phase379 runs frozen Phase333 native-funded matched-cap component A/B/C twice, enforcing byte-identical JSON. The Phase333 result is **not** a seven-slot champion and never opens external benchmarks.
5. Always upload V98-only JSON/log artifacts, including failed provenance; never commit or push automatically. A missing source, blocked vendor, mismatched zero-rate events, runner failure, or any failed test is a fail-closed result, not evidence of performance.

A PASS does not establish a complete composed engine; a full seven-slot internally frozen candidate must pass separate chronological validation before comparison with external benchmarks. No rejected hypothesis is eligible for rescue.
