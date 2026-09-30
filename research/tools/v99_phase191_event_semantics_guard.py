#!/usr/bin/env python3
"""DATA_ONLY semantic guard for Phase191 stablecoin event ingestion.

No price/PnL/holdout imports. Encodes issuer-specific event rules and fails closed
on attempts to treat zero-address Transfer as a universal mint/burn primitive.
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


def validate(events: Iterable[Event]) -> dict:
    seen = set()
    counts = {"USDC_Mint": 0, "USDC_Burn": 0, "USDT_Issue": 0, "USDT_Redeem": 0}
    usdc_native_mint = usdc_native_burn = 0
    usdc_zero_mint = usdc_zero_burn = 0

    for e in events:
        if e.amount <= 0 or e.block_number < 0 or e.timestamp <= 0:
            raise ValueError("invalid immutable event fields")
        if e.key in seen:
            raise ValueError(f"duplicate log identity: {e.key}")
        seen.add(e.key)
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

    # Reconciliation is only asserted when both representations were supplied.
    if usdc_native_mint and usdc_zero_mint and usdc_native_mint != usdc_zero_mint:
        raise ValueError("USDC mint reconciliation failed")
    if usdc_native_burn and usdc_zero_burn and usdc_native_burn != usdc_zero_burn:
        raise ValueError("USDC burn reconciliation failed")
    return counts


def self_test() -> None:
    h = "0x" + "1" * 64
    tx = "0x" + "2" * 64
    base = dict(block_number=1, block_hash=h, tx_hash=tx, timestamp=1)
    ok = [Event(USDT, "Issue", 10, log_index=0, **base), Event(USDC, "Mint", 20, log_index=1, **base)]
    assert validate(ok)["USDT_Issue"] == 10
    try:
        validate([Event(USDT, "Transfer", 10, log_index=2, from_address=ZERO, to_address="0x"+"3"*40, **base)])
    except ValueError:
        pass
    else:
        raise AssertionError("USDT zero-address semantic guard failed")

if __name__ == "__main__":
    self_test()
    print("PASS: Phase191 issuer-specific event semantics guard")
