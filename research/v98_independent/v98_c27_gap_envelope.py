"""C27 ex-ante gap-risk feasibility, independent of all trading returns.

A causal queued sell cannot enforce a hard cap at the next opening under
unbounded price gaps. This module computes the maximum post-gap exposure
given an explicit stress envelope; it never looks at realized C27 PnL.
"""
import math

def worst_long_weight(pre_gap_weight, up_gap, down_gap):
    """Worst concentration when the selected asset rises and others fall.

    Cash remains unchanged. All weights are fractions of equity, long-only.
    """
    w=float(pre_gap_weight)
    if not (0 <= w <= 1 and up_gap >= 0 and 0 <= down_gap < 1):
        raise ValueError("C27_INVALID_GAP_ENVELOPE")
    numerator=w*(1+up_gap)
    denominator=numerator+(1-w)*(1-down_gap)
    return numerator/denominator

def preemptive_asset_cap(hard_cap=.40, up_gap=.20, down_gap=.20):
    """Largest previous-open weight surviving the declared asymmetric shock."""
    if not (0<hard_cap<1 and up_gap>=0 and 0<=down_gap<1):
        raise ValueError("C27_INVALID_GAP_ENVELOPE")
    up=1+up_gap
    down=1-down_gap
    return hard_cap*down/(up*(1-hard_cap)+hard_cap*down)

def preemptive_gross_cap(hard_cap=.90, up_gap=.20):
    """Largest gross exposure surviving all-assets-up shock with static cash."""
    if not (0<hard_cap<1 and up_gap>=0):
        raise ValueError("C27_INVALID_GAP_ENVELOPE")
    return hard_cap/(1+up_gap*(1-hard_cap))

def prove_envelope(asset_cap, gross_cap, up_gap=.20, down_gap=.20):
    if asset_cap>preemptive_asset_cap(.40,up_gap,down_gap)+1e-12:
        raise ValueError("C27_ASSET_ENVELOPE_UNPROVEN")
    if gross_cap>preemptive_gross_cap(.90,up_gap)+1e-12:
        raise ValueError("C27_GROSS_ENVELOPE_UNPROVEN")
    return True
