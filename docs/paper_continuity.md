# Official paper execution continuity

The workflow now uses independent operational adapters ending in `_incremental.py`. The frozen research/backtest implementations and strategy parameters remain unchanged. The operational executor is regression-tested against the frozen executor before any checkpoint is supplied.

Each published ledger stores its full precision execution checkpoint: equity, holdings, previous requested target, last prices, drawdown peak, guard activation and cooldown. V99 stores both sleeve checkpoints, sleeve capitals and the remaining monthly allocation schedule. Only hours after the durable checkpoint are executed; the old equity curve and decision records are copied exactly and remain protected by the original publication verifier.

Legacy files did not contain the full internal execution state. The one-time migration restores recorded capital and holdings; missing guard internals are reconstructed from the published equity curve. V99 satellite holdings are inferred from its recorded aggregate holdings, parent holdings and sleeve allocation. This limitation is disclosed in checkpoint migration metadata and must not be described as exact legacy internal-state recovery.

A catch-up longer than three hours is marked RETROSPECTIVE_GAP_RECOVERY, with its old boundary, new boundary and computation time. An independent forward validation boundary is recorded at migration/catch-up time. These catch-up hours are not uninterrupted contemporaneous forward evidence.

The freshness monitor checks actual published timestamps and reports a failed check if publication remains stale for over three hours, even when retries are active. Missing market hours, held symbols or changed execution parameters stop publication. Repeated execution of the same hour is idempotent. No real orders are enabled.
