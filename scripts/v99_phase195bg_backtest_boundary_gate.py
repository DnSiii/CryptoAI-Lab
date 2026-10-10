"""Read-only V99 research paper/backtest boundary firewall; never permits promotion."""
import json
import sys
import zipfile
from datetime import datetime, timedelta

NAMES = ('r98','f1','f3','f7','f12')
PATH = 'reports/paper_v99_research_ledger.json'


def utc(value):
    t = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if t.tzinfo is None or t.utcoffset() != timedelta(0):
        raise ValueError('explicit UTC required')
    return t


def indexed(rows, hourly=False):
    out = {}
    last = None
    for row in rows:
        t = utc(row['timestamp'])
        if last is not None and (t <= last or (hourly and t-last != timedelta(hours=1))):
            raise ValueError('duplicate, unordered or gapped timestamps')
        out[t] = row
        last = t
    if not out:
        raise ValueError('empty curve')
    return out


def read(path):
    with zipfile.ZipFile(path) as z:
        return json.loads(z.read(PATH),parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON')))


def audit(old, new):
    for item in (old,new):
        if item.get('mode') != 'PAPER_ONLY' or item.get('real_orders_enabled') is not False:
            raise ValueError('paper-only required')
        if set(item['variants']) != set(NAMES):
            raise ValueError('five fixed variants required')
    boundary = utc(old['paper_start_after_timestamp'])
    if boundary != utc(new['paper_start_after_timestamp']):
        raise ValueError('paper boundary moved')
    if utc(new['latest_data_timestamp']) < utc(old['latest_data_timestamp']):
        raise ValueError('data moved backwards')
    report = {}
    for name in NAMES:
        old_p = indexed(old['variants'][name]['equity_curve'],True)
        new_p = indexed(new['variants'][name]['equity_curve'],True)
        if next(iter(old_p)) != boundary or next(iter(new_p)) != boundary:
            raise ValueError('paper curve must begin at boundary')
        old_b = indexed(old['backtest_reference'][name]['curve'])
        new_b = indexed(new['backtest_reference'][name]['curve'])
        old_paper_keys=set(old_p);new_paper_keys=set(new_p)
        common_paper=old_paper_keys & new_paper_keys
        historical=set(old_b)&set(new_b)
        changed_pre=[t for t in historical if t < boundary and old_b[t]!=new_b[t]]
        changed_paper=[t for t in common_paper if old_p[t]!=new_p[t]]
        forward_mislabeled=[t for t in new_b if t >= boundary]
        report[name]={
            'pre_paper_backtest_rewrites':len(changed_pre),
            'first_pre_paper_rewrite':min(changed_pre).isoformat() if changed_pre else None,
            'forward_points_mislabeled_backtest':len(forward_mislabeled),
            'rewritten_paper_hours':len(changed_paper),
            'missing_paper_hours':len(old_paper_keys-new_paper_keys),
        }
    hold=any(any(row[k] for k in ('pre_paper_backtest_rewrites','forward_points_mislabeled_backtest','rewritten_paper_hours','missing_paper_hours')) for row in report.values())
    return {'status':'DATA_ONLY_HOLD' if hold else 'OBSERVED_ONLY_NOT_PROMOTION',
            'publication_authorized':False,'promotion_authorized':False,
            'boundary':boundary.isoformat(),'variants':report}


if __name__=='__main__':
    print(json.dumps(audit(read(sys.argv[1]),read(sys.argv[2])),indent=2))
