#!/usr/bin/env python3
"""DATA_ONLY semantic guard for Phase191 stablecoin event ingestion.

No price/PnL/holdout imports. Encodes issuer-specific event rules and fails closed
on attempts to treat zero-address Transfer as a universal mint/burn primitive.
Synthetic fixtures only: this guard does not create an economic trial.
"""
from dataclasses import dataclass
from typing import Iterable

ZERO = "0x" + "0" * 40
USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
USDT = "0xdac17f958d2ee523a2206206994597c13d831ec7"

@dataclass(frozen=True)
class Event:
    token: str
    kind: str
    amount: int
    block_number: int
    block_hash: str
    tx_hash: str
    log_index: int
    timestamp: int
    from_address: str = ""
    to_address: str = ""

    @property
    def key(self):
        return (self.block_hash.lower(), self.tx_hash.lower(), self.log_index)


def _hash_ok(value: str) -> bool:
    if len(value) != 66 or not value.startswith("0x"):
        return False
    try:
        int(value[2:], 16)
    except ValueError:
        return False
    return True


def validate(events: Iterable[Event]) -> dict:
    seen = set()
    height_hash = {}
    last_order = None
    counts = {"USDC_Mint": 0, "USDC_Burn": 0, "USDT_Issue": 0, "USDT_Redeem": 0}
    usdc_native_mint = usdc_native_burn = 0
    usdc_zero_mint = usdc_zero_burn = 0

    for e in events:
        if e.amount <= 0 or e.block_number < 0 or e.timestamp <= 0 or e.log_index < 0:
            raise ValueError("invalid immutable event fields")
        if not _hash_ok(e.block_hash) or not _hash_ok(e.tx_hash):
            raise ValueError("malformed immutable provenance hash")
        if e.key in seen:
            raise ValueError(f"duplicate log identity: {e.key}")
        seen.add(e.key)
        bh = e.block_hash.lower()
        old = height_hash.setdefault(e.block_number, bh)
        if old != bh:
            raise ValueError("conflicting block hash at same height")
        order = (e.block_number, e.log_index)
        if last_order is not None and order <= last_order:
            raise ValueError("events must be strictly ordered by block/log index")
        last_order = order
        token = e.token.lower()

        if token == USDT:
            if e.kind == "Issue": counts["USDT_Issue"] += e.amount
            elif e.kind == "Redeem": counts["USDT_Redeem"] += e.amount
            elif e.kind == "Transfer" and (e.from_address.lower() == ZERO or e.to_address.lower() == ZERO):
                raise ValueError("USDT zero-address Transfer cannot define issuance/redemption")
        elif token == USDC:
            if e.kind == "Mint":
                counts["USDC_Mint"] += e.amount; usdc_native_mint += e.amount
            elif e.kind == "Burn":
                counts["USDC_Burn"] += e.amount; usdc_native_burn += e.amount
            elif e.kind == "Transfer":
                if e.from_address.lower() == ZERO: usdc_zero_mint += e.amount
                if e.to_address.lower() == ZERO: usdc_zero_burn += e.amount
        else:
            raise ValueError(f"unapproved contract: {e.token}")

    if usdc_native_mint and usdc_zero_mint and usdc_native_mint != usdc_zero_mint:
        raise ValueError("USDC mint reconciliation failed")
    if usdc_native_burn and usdc_zero_burn and usdc_native_burn != usdc_zero_burn:
        raise ValueError("USDC burn reconciliation failed")
    return counts


def lagged_net_by_block(events: Iterable[Event]) -> dict:
    """Build a causal t-1 net-flow feature from already validated ordered events.

    Output at block b contains cumulative signed flow through blocks strictly < b.
    This is an invariant helper only; it has no market/price inputs.
    """
    evs = list(events)
    validate(evs)
    signed = {}
    for e in evs:
        token = e.token.lower()
        delta = 0
        if token == USDC and e.kind == "Mint": delta = e.amount
        elif token == USDC and e.kind == "Burn": delta = -e.amount
        elif token == USDT and e.kind == "Issue": delta = e.amount
        elif token == USDT and e.kind == "Redeem": delta = -e.amount
        signed[e.block_number] = signed.get(e.block_number, 0) + delta
    out = {}
    cumulative = 0
    for block in sorted(signed):
        out[block] = cumulative
        cumulative += signed[block]
    return out


def _must_fail(events, needle: str) -> None:
    try:
        validate(events)
    except ValueError as exc:
        assert needle in str(exc), (needle, str(exc))
    else:
        raise AssertionError(f"expected failure containing: {needle}")


def self_test() -> None:
    h1 = "0x" + "1" * 64
    h2 = "0x" + "2" * 64
    h3 = "0x" + "3" * 64
    tx1 = "0x" + "4" * 64
    tx2 = "0x" + "5" * 64
    tx3 = "0x" + "6" * 64
    e1 = Event(USDT, "Issue", 10, 10, h1, tx1, 0, 100)
    e2 = Event(USDC, "Mint", 20, 11, h2, tx2, 0, 110)
    e3 = Event(USDT, "Redeem", 3, 12, h3, tx3, 0, 120)
    assert validate([e1, e2, e3]) == {"USDC_Mint":20,"USDC_Burn":0,"USDT_Issue":10,"USDT_Redeem":3}
    assert lagged_net_by_block([e1, e2, e3]) == {10:0, 11:10, 12:30}

    zero_usdt = Event(USDT, "Transfer", 10, 10, h1, tx1, 1, 100, ZERO, "0x"+"7"*40)
    _must_fail([zero_usdt], "USDT zero-address")
    _must_fail([e1, e1], "duplicate log identity")
    conflict = Event(USDC, "Mint", 1, 10, h2, tx2, 1, 101)
    _must_fail([e1, conflict], "conflicting block hash")
    _must_fail([e2, e1], "strictly ordered")
    malformed = Event(USDC, "Mint", 1, 13, "0x1234", tx3, 0, 130)
    _must_fail([malformed], "malformed immutable provenance hash")

    # Reconciliation must fail closed when native and zero-address views disagree.
    usdc_native = Event(USDC, "Mint", 20, 20, h1, tx1, 0, 200)
    usdc_zero = Event(USDC, "Transfer", 19, 21, h2, tx2, 0, 210, ZERO, "0x"+"8"*40)
    _must_fail([usdc_native, usdc_zero], "USDC mint reconciliation failed")

if __name__ == "__main__":
    self_test()
    print("PASS: Phase191 issuer-specific semantics, provenance/order and causal t-1 guard")
