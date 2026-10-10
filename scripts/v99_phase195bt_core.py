"""Research-only paper accounting checks. No promotion."""
from datetime import datetime,timedelta

def audit(d):
    if d.get('mode')!='PAPER_ONLY':raise ValueError('paper-only')
    base=d['base_capital_brl'];prev=base;last=None;errors=[]
    for r in d['equity_curve']:
        t=datetime.fromisoformat(r['timestamp'].replace('Z','+00:00'))
        if t.utcoffset()!=timedelta(0):raise ValueError('UTC')
        if last and t-last!=timedelta(hours=1):errors.append('time')
        cap=r['capital_brl'];hour=r['hour_result_brl']
        if abs(cap-prev-hour)>.011:errors.append('capital')
        if abs(cap-base*r['equity_multiple'])>.011:errors.append('multiple')
        if 'gross_result_brl' in r:
            if abs(r['gross_result_brl']-r['total_cost_brl']-r['net_result_brl'])>.011:errors.append('net')
            if abs(r['fees_brl']-r['funding_result_brl']-r['total_cost_brl'])>.011:errors.append('funding')
        prev=cap;last=t
    return errors
