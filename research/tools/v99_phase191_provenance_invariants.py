#!/usr/bin/env python3
"""DATA_ONLY provenance invariants for Phase191 chain-native stablecoin events.

No price/PnL/holdout access. This gate is intentionally independent of the
economic layer and fails closed on non-finalized, malformed, duplicate, or
non-monotone chain provenance.
"""
from dataclasses import dataclass
from typing import Iterable

USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
USDT = "0xdac17f958d2ee523a2206206994597c13d831ec7"
APPROVED = {USDC, USDT}

@dataclass(frozen=True)
class ChainEvent:
    token: str
    block_number: int
    block_hash: str
    tx_hash: str
    log_index: int
    timestamp: int
    finalized: bool

    @property
    def identity(self):
        return (self.block_hash.lower(), self.tx_hash.lower(), self.log_index)


def _is_hash(value: str) -> bool:
    if not isinstance(value, str) or len(value) != 66 or not value.startswith("0x"):
        return False
    try:
        int(value[2:], 16)
        return True
    except ValueError:
        return False


def validate_provenance(events: Iterable[ChainEvent]) -> dict:
    rows = list(events)
    if not rows:
        raise ValueError("empty provenance sample")
    seen = set()
    last = None
    blocks = {}
    for e in rows:
        token = e.token.lower()
        if token not in APPROVED:
            raise ValueError("unapproved contract")
        if not e.finalized:
            raise ValueError("non-finalized event")
        if e.block_number < 0 or e.log_index < 0 or e.timestamp <= 0:
            raise ValueError("invalid chain coordinates")
        if not _is_hash(e.block_hash) or not _is_hash(e.tx_hash):
            raise ValueError("malformed immutable hash")
        if e.identity in seen:
            raise ValueError("duplicate log identity")
        seen.add(e.identity)
        prior_hash = blocks.setdefault(e.block_number, e.block_hash.lower())
        if prior_hash != e.block_hash.lower():
            raise ValueError("conflicting block hash at same height")
        coord = (e.block_number, e.log_index)
        if last is not None and coord < last:
            raise ValueError("non-monotone chain order")
        last = coord
    return {"rows": len(rows), "blocks": len(blocks), "contracts": len({e.token.lower() for e in rows})}


def self_test() -> None:
    h1 = "0x" + "1" * 64
    h2 = "0x" + "2" * 64
    tx1 = "0x" + "3" * 64
    tx2 = "0x" + "4" * 64
    ok = [
        ChainEvent(USDC, 100, h1, tx1, 0, 1700000000, True),
        ChainEvent(USDT, 101, h2, tx2, 0, 1700000012, True),
    ]
    assert validate_provenance(ok) == {"rows": 2, "blocks": 2, "contracts": 2}
    for bad in [
        [ChainEvent(USDC, 100, h1, tx1, 0, 1700000000, False)],
        ok + [ok[0]],
        [ok[1], ok[0]],
    ]:
        try:
            validate_provenance(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("provenance fail-closed invariant failed")

if __name__ == "__main__":
    self_test()
    print("PASS: Phase191 finalized provenance invariants")
