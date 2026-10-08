# Phase195-O preregistration: Beacon archive diagnostics

Fixed historical TRAIN slot 6173989. Keep the same two providers: EthStaker and ChainSafe. Probe exactly two endpoints per provider: /eth/v1/beacon/headers/finalized (liveness control) and /eth/v1/beacon/headers/6173989 (historical header). Record HTTP status, error class and exact historical slot when returned. Distinguish provider outage from missing archive history. This is DATA_ONLY; operator-reported flags do not authenticate consensus ancestry. No economic tests, no promotion, no holdout access or frozen modifications.
