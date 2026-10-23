"""C149 independent read-only model journal oracle; NEVER exchange authentication.
No imports from journal constructor, reconciler, or strategy. Synthetic/model-only.
"""
from datetime import timedelta
from decimal import Decimal, InvalidOperation

ASSETS = ('BTC', 'ETH')
STRESS = {'severe_model_only': Decimal('0.0007'),
          'supersevere_model_only': Decimal('0.0014')}


def d(x):
    if type(x) is not str or x.strip() != x:
        raise ValueError('C149_NONCANONICAL_AMOUNT')
    try:
        n = Decimal(x)
    except InvalidOperation as exc:
        raise ValueError('C149_BAD_AMOUNT') from exc
    if not n.is_finite():
        raise ValueError('C149_NONFINITE_AMOUNT')
    return n


def state(row):
    if type(row) is not dict or set(row) != {'cash_quote','spot_base','perp_base'}:
        raise ValueError('C149_ACCOUNT_SCHEMA')
    if any(type(row[k]) is not dict or set(row[k]) != set(ASSETS)
           for k in ('spot_base','perp_base')):
        raise ValueError('C149_ASSET_SCHEMA')
    cash=d(row['cash_quote'])
    spot={a:d(row['spot_base'][a]) for a in ASSETS}
    perp={a:d(row['perp_base'][a]) for a in ASSETS}
    if cash < 0 or any(x < 0 for x in spot.values()):
        raise ValueError('C149_UNCOLLATERALIZED_ACCOUNT')
    return cash,spot,perp


def oracle(journal, initial_marks, initial_marks_time, scenario):
    """Re-execute modeled hourly cash/positions/fees/funding, never authenticate."""
    if scenario not in STRESS:
        raise ValueError('C149_UNKNOWN_SCENARIO')
    frames=journal['frames']
    if not frames:
        raise ValueError('C149_EMPTY')
    previous=initial_marks
    previous_time=initial_marks_time
    previous_after=None
    initial_nav=None
    total_variation=total_funding=total_fees=Decimal('0')
    total_fills=total_funding_events=0
    for frame in frames:
        t=frame['time']
        if t != previous_time+timedelta(hours=1):
            raise ValueError('C149_HOUR_GAP')
        marks=frame['marks']
        if set(marks)!=set(ASSETS) or any(set(marks[a])!={'spot','perp'} for a in ASSETS):
            raise ValueError('C149_MARK_SCHEMA')
        for a in ASSETS:
            for leg in ('spot','perp'):
                if d(marks[a][leg])<=0 or d(previous[a][leg])<=0:
                    raise ValueError('C149_BAD_MARK')
        before=state(frame['before'])
        after_mark=state(frame['after_mark'])
        after_funding=state(frame['after_funding'])
        after=state(frame['after'])
        if previous_after is not None and before!=previous_after:
            raise ValueError('C149_DISCONTINUOUS_ACCOUNT')
        if initial_nav is None:
            initial_nav=before[0]+sum(before[1][a]*d(previous[a]['spot']) for a in ASSETS)
        variation=sum((before[2][a]*(d(marks[a]['perp'])-d(previous[a]['perp'])) for a in ASSETS),Decimal('0'))
        if after_mark[0]!=before[0]+variation or after_mark[1:]!=before[1:]:
            raise ValueError('C149_VARIATION_MARGIN')
        funding=Decimal('0'); seen=set()
        for ev in frame['funding']:
            if (set(ev)!={'asset','time','rate','source','instrument'} or
                ev['asset'] not in ASSETS or ev['asset'] in seen or ev['time']!=t or
                ev['source']!='OKX' or ev['instrument']!=ev['asset']+'-USDT-SWAP'):
                raise ValueError('C149_FUNDING_SCHEMA')
            a=ev['asset']; rate=d(ev['rate'])
            if abs(rate)>Decimal('.1'):
                raise ValueError('C149_FUNDING_RATE')
            funding-=before[2][a]*d(marks[a]['perp'])*rate
            seen.add(a)
        if after_funding[0]!=after_mark[0]+funding or after_funding[1:]!=after_mark[1:]:
            raise ValueError('C149_FUNDING_CASH')
        running=after_funding
        for fill in frame['fills']:
            if fill['time']!=t or state(fill['before'])!=running:
                raise ValueError('C149_FILL_CHAIN')
            a=fill['asset']; leg=fill['leg']; side=fill['side']
            if a not in ASSETS or leg not in ('spot','perp') or side not in ('buy','sell'):
                raise ValueError('C149_FILL_SCHEMA')
            qty=d(fill['base_quantity']); price=d(fill['execution_price_quote_per_base'])
            notional=d(fill['quote_notional']); native=d(fill['native_fee_quote'])
            stress=d(fill['stress_fee_quote']); base_fee=d(fill['base_fee_units'])
            if (qty<=0 or price<=0 or notional!=qty*price or
                price!=d(marks[a][leg]) or native<0 or native>notional*Decimal('.01') or
                stress!=notional*STRESS[scenario] or base_fee<0 or
                base_fee*price not in (Decimal('0'),native)):
                raise ValueError('C149_FILL_FEE_OR_MARK')
            direction=Decimal('1') if side=='buy' else Decimal('-1')
            cash,spot,perp=running
            new_cash=cash; new_spot=spot.copy(); new_perp=perp.copy()
            if leg=='spot':
                new_cash-=direction*notional+stress+(Decimal('0') if base_fee else native)
                new_spot[a]+=direction*qty-base_fee
            else:
                if base_fee:
                    raise ValueError('C149_PERP_BASE_FEE')
                new_cash-=native+stress
                new_perp[a]+=direction*qty
            nxt=state(fill['after'])
            if nxt!=(new_cash,new_spot,new_perp):
                raise ValueError('C149_FILL_BALANCE')
            if d(fill['booked_total_fee_quote'])!=native+stress:
                raise ValueError('C149_BOOKED_FEE')
            running=nxt
            total_fees+=native+stress
            total_fills+=1
        if running!=after:
            raise ValueError('C149_FINAL_ACCOUNT')
        if any(after[1][a]+after[2][a]!=0 for a in ASSETS):
            raise ValueError('C149_UNHEDGED_BASE')
        nav=after[0]+sum(after[1][a]*d(marks[a]['spot']) for a in ASSETS)
        if nav<=0:
            raise ValueError('C149_NONPOSITIVE_NAV')
        gross=sum(after[1][a]*(d(marks[a]['spot'])+d(marks[a]['perp'])) for a in ASSETS)
        if gross>nav+Decimal('1e-18'):
            raise ValueError('C149_GROSS_CAP')
        total_variation+=variation
        total_funding+=funding
        total_funding_events+=len(seen)
        previous=marks; previous_time=t; previous_after=after
    proof=journal['account_proof']
    expected={'hours_replayed':len(frames),'fills_replayed':total_fills,
              'funding_events_modeled':total_funding_events,
              'perp_variation_margin_quote':str(total_variation),
              'modeled_funding_quote':str(total_funding),
              'modeled_native_plus_stress_fees_quote':str(total_fees)}
    for k,v in expected.items():
        if (proof.get(k)!=v if isinstance(v,int) else d(proof.get(k))!=d(v)):
            raise ValueError('C149_SUMMARY_PROOF_MISMATCH_'+k)
    if state(proof['last_declared_account_state'])!=previous_after:
        raise ValueError('C149_FINAL_PROOF_MISMATCH')
    final_nav=previous_after[0]+sum(previous_after[1][a]*d(previous[a]['spot']) for a in ASSETS)
    if d(proof['modeled_net_nav_delta_quote'])!=final_nav-initial_nav:
        raise ValueError('C149_NAV_DELTA_PROOF_MISMATCH')
    return {'status':'C149_INDEPENDENT_SYNTHETIC_ONLY','scenario':scenario,
            'hours':len(frames),'modeled_fills':total_fills,
            'modeled_funding_events':total_funding_events,
            'max_accounting_residual':'0','exchange_authenticated':False,
            'historical_roi_authorized':False,'promotion_authorized':False}
