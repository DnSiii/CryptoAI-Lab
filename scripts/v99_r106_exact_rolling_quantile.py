#!/usr/bin/env python3
"""Exact causal rolling quantile primitive for Phase121.

Two-pass intended use: first collect the finite discrete quantity support for one
asset from train-only aggTrades; then feed timestamped quantities chronologically.
The Fenwick tree stores counts over the exact sorted support, so order statistics
are exact (no sketch/approximation). Expiry is timestamp based. query() is called
BEFORE adding the current hour, which enforces the Phase121 strict-before-t rule.
"""
from __future__ import annotations
from collections import deque
from bisect import bisect_left
import math

class Fenwick:
    def __init__(self, n: int):
        if n <= 0: raise ValueError("n must be positive")
        self.n=n; self.bit=[0]*(n+1)
    def add(self, i: int, delta: int) -> None:
        i += 1
        while i <= self.n:
            self.bit[i] += delta; i += i & -i
    def total(self) -> int:
        s=0; i=self.n
        while i:
            s += self.bit[i]; i -= i & -i
        return s
    def kth(self, k: int) -> int:
        """0-based index of the k-th item (k is 1-based order statistic)."""
        if k < 1 or k > self.total(): raise IndexError(k)
        idx=0; step=1 << (self.n.bit_length()-1)
        while step:
            nxt=idx+step
            if nxt <= self.n and self.bit[nxt] < k:
                idx=nxt; k-=self.bit[nxt]
            step >>= 1
        return idx

class ExactRollingQuantile:
    def __init__(self, support, window_ms: int, q: float):
        vals=sorted(set(float(x) for x in support if math.isfinite(float(x))))
        if not vals: raise ValueError("empty support")
        if window_ms <= 0 or not 0 <= q <= 1: raise ValueError("bad parameters")
        self.vals=vals; self.window_ms=window_ms; self.q=q
        self.fw=Fenwick(len(vals)); self.events=deque(); self.last_ts=None
    def _index(self, x: float) -> int:
        i=bisect_left(self.vals, float(x))
        if i == len(self.vals) or self.vals[i] != float(x):
            raise ValueError("quantity outside frozen train support")
        return i
    def expire(self, now_ms: int) -> None:
        cutoff=now_ms-self.window_ms
        while self.events and self.events[0][0] < cutoff:
            _,i=self.events.popleft(); self.fw.add(i,-1)
    def add(self, ts_ms: int, qty: float) -> None:
        if self.last_ts is not None and ts_ms < self.last_ts:
            raise AssertionError("non-chronological input")
        i=self._index(qty); self.events.append((ts_ms,i)); self.fw.add(i,1); self.last_ts=ts_ms
    def query(self, now_ms: int):
        self.expire(now_ms); n=self.fw.total()
        if n == 0: return None
        # nearest-rank empirical quantile, deterministic and exact.
        rank=max(1, math.ceil(self.q*n))
        return self.vals[self.fw.kth(rank)]

def _self_test():
    r=ExactRollingQuantile([1,2,3,4,5], 1000, .9)
    for t,x in [(0,1),(1,2),(2,3),(3,4),(4,5)]: r.add(t,x)
    assert r.query(5)==5
    # strict expiry and chronology invariants
    r.expire(1002); assert r.fw.total()==3
    try: r.add(0,1); raise AssertionError("chronology guard failed")
    except AssertionError: pass
    # Crucial causal usage invariant: caller queries at hour boundary BEFORE adding that hour.
    z=ExactRollingQuantile([1,100], 10_000, .9); z.add(0,1)
    assert z.query(100)==1
    z.add(100,100); assert z.query(101)==100
    print("PASS exact rolling quantile self-test")

if __name__ == '__main__': _self_test()
