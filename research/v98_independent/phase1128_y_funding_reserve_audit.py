#!/usr/bin/env python3
"""Independent counterexample to Y basket-stop funding-reserve omission.

Synthetic FORMAL-contract witness only. Funding rate is deliberately extreme;
this is not a historical frequency or return claim and is not a parameter tune.
"""
import json
import numpy as np
from phase1123_y_continuous_feedback import evaluate,FUNDING_EVENTS

def audit():
    p=np.ones(4)*100;u=np.array([10.,0,0,0]);cash=9000.
    down=np.ones(4)*.1;up=np.ones(4)*.1
    funding=np.array([7399/6600,0,0,0]);quote=np.ones(4)*1e9
    r=evaluate(1.,p,p,u,cash,down,up,funding,quote,.002,.002,details=True)
    reserve=float(FUNDING_EVENTS*np.sum(np.abs(u)*funding*(1+up)*p))
    true_exit=float(r['basket_exit_equity']-reserve)
    floor=float(.25*r['prior_equity'])
    return {'source_accepts':bool(r['ok']),'source_exit':r['basket_exit_equity'],
        'reserved_funding':reserve,'true_exit_after_reserve':true_exit,
        'floor':floor,'uncertified_exit':bool(r['ok'] and true_exit<floor),
        'synthetic_only':True,'historical_pnl_computed':False}

if __name__=='__main__':print(json.dumps(audit(),sort_keys=True))
