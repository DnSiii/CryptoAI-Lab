#!/usr/bin/env python3
"""Independent arithmetic audit for future-only V98 capital competition.
No historical PnL, no training data, no rejected-candidate rescue.
"""
import itertools,math
import numpy as np
from v98_future_net_growth_capital_competition import allocate

def oracle(core,sleeves,old,r,f,fee,slippage,cap=.84):
    # Independently reconstruct EWMA and shrinkage without calling forecast().
    ages=np.arange(335,-1,-1,dtype=float)
    w=2.**(-ages/84.)
    w=w/float(np.sum(w))
    means=np.sum(r*w[:,None],axis=0)
    deviations=r-means
    matrix=np.zeros((4,4))
    for j in range(4):
        for k in range(4):
            matrix[j,k]=float(np.dot(w,deviations[:,j]*deviations[:,k]))
    for j in range(4):
        for k in range(4):
            if j!=k:matrix[j,k]*=.5
    funding_hourly=np.mean(f,axis=0)/8.
    result=[]
    for factors in itertools.product((0.,.5,1.),repeat=3):
        opt=sleeves*np.array(factors)[:,None]
        gross_opt=float(sum(abs(float(x)) for x in opt.flat))
        if gross_opt>cap+1e-10:continue
        gross_core=float(np.sum(np.abs(core)))
        scaled_core=core*min(1.,(cap-gross_opt)/gross_core) if gross_core>0 else core.copy()
        net=scaled_core+opt.sum(axis=0)
        virtual=float(np.abs(scaled_core).sum()+np.abs(opt).sum())
        turnover=float(np.abs(net-old).sum())
        variance=float(np.dot(net,matrix@net))
        utility=168.*(float(np.dot(net,means))-float(np.dot(net,funding_hourly))-
                      .5*max(0.,variance))-(fee+slippage)*turnover
        result.append((utility,turnover,virtual,factors,net))
    result.sort(key=lambda x:(-x[0],x[1],x[2],x[3]))
    return result[0]

def test():
    rng=np.random.default_rng(980301)
    for i in range(200):
        r=rng.normal(0,.002,(336,4))
        f=rng.normal(0,.0004,(21,4))
        core=rng.uniform(0,.15,4)
        sleeves=rng.uniform(-.1,.1,(3,4))
        old=rng.uniform(-.18,.18,4)
        fee=.0004;slip=.0002
        primary=allocate(core,sleeves,old,r,f,fee,slip)
        independent=oracle(core,sleeves,old,r,f,fee,slip)
        if primary['factors']!=independent[3]:
            raise ValueError('V98_INDEPENDENT_GROWTH_ACTION_MISMATCH_'+str(i))
        if not np.allclose(primary['net_weights'],independent[4],rtol=0,atol=1e-12):
            raise ValueError('V98_INDEPENDENT_GROWTH_NET_MISMATCH_'+str(i))
        if not math.isclose(primary['expected_net_log_utility'],independent[0],
                            rel_tol=1e-11,abs_tol=1e-12):
            raise ValueError('V98_INDEPENDENT_GROWTH_UTILITY_MISMATCH_'+str(i))
        # Mutating observations AFTER the 336h / 21-event cutoff is irrelevant.
        future_r=rng.normal(0,.02,(30,4))
        future_f=rng.normal(0,.01,(8,4))
        joined_r=np.vstack((r,future_r));joined_f=np.vstack((f,future_f))
        joined_r[336:]*=-10.;joined_f[21:]*=20.
        same=allocate(core,sleeves,old,joined_r[:336],joined_f[:21],fee,slip)
        if same['factors']!=primary['factors'] or not np.array_equal(
                same['net_weights'],primary['net_weights']):
            raise ValueError('V98_INDEPENDENT_GROWTH_FUTURE_MUTATION')
    return {'decision':'PASS_INDEPENDENT_EXPECTED_NET_LOG_UTILITY_ARITHMETIC_ONLY',
            'synthetic_cases':200,'action_mismatches':0,'net_weight_mismatches':0,
            'utility_mismatches':0,'future_mutation_mismatches':0,
            'historical_pnl_computed':False,'holdout_accessed':False,
            'not_a_validated_engine':True}
if __name__=='__main__':
    import json
    print(json.dumps(test(),sort_keys=True))
