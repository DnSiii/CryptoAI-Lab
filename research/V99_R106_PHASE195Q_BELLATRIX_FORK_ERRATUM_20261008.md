# Phase195-Q fork-specific prereg correction (before implementation)

The fixed TRAIN slot 6173989 is epoch 192937 (2023-04-07), which precedes the Capella fork epoch 194048. Therefore Phase195-Q MUST decode a Bellatrix SignedBeaconBlock and Bellatrix ExecutionPayload, not Capella. Reject Capella/withdrawals assumptions. Preserve the fixed block number, hash and receipts root, and compare against the independent Era record without tuning. This correction precedes any Phase195-Q execution. Archive data remains unanchored until a trusted historical-root proof is verified.
