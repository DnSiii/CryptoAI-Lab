# V99 paper continuity alert — 2026-10-08

The official multi-engine paper refresh is repeatedly failing at the published-history invariant. Run 37826227784 reported: Published equity_curve was rewritten; recovery publication blocked. This is an appropriate fail-closed safeguard, not evidence of a successful official paper update.

The separate V99 five-variant forward-paper workflow 37817608480 succeeded, and the durable paper-results / gh-pages V99 research comparison remains byte-identical at 2026-10-08 17:45 UTC. Do not conflate these two pipelines.

Official paper heartbeat is still dated 2026-10-01. Preserve existing official paper history; investigate deterministic replay drift before any append or new ledger version. No retrospective rewrite, Frozen edits or promotion authorized.
