# V98 Independent Phase243 — source capture release readiness (2026-10-11 12:46 BRT)

DATA_ONLY. Branch research/v98-independent-zero. No 2026+ holdout, no V16/V99 reads or writes, no alpha promotion.

The current phase243_xrp_source_capture.py has a literal double-escaped CHECKSUM regex: the original provider sidecar does not match it. Its relative ROOT also depends on caller working directory. A tested V98-only patch corrects both, bounds response types/sizes, and explicitly distinguishes a publisher checksum from a signature.

Offline source-capture and monthly-original contract tests (prior V98 local evidence bundle) passed. The original 2023-11 XRP monthly 1h ZIP is checksum-matched, but the 2023-11-14 11:00 UTC bar remains physically contradictory. Do not repair or choose a preferred bar from PnL.

Next reproducible data-only action: apply tested patch to phase243_xrp_source_capture.py; execute the source capture on an authenticated runner; preserve original monthly 1h, daily 1h and daily 1m ZIPs plus sidecars and manifests; compare all 24 daily hours to minute aggregates under frozen preregistered tolerances. If unavailable or inconsistent, remain BLOCKED_SOURCE_CONFLICT / NO_CHAMPION.

Phase240 rejected; Phase243 blocked; no new historical backtest or holdout access.
