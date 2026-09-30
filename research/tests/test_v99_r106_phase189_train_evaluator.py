import csv,datetime,importlib.util,pathlib,tempfile
P=pathlib.Path(__file__).parents[1]/'tools'/'v99_r106_phase189_train_evaluator.py';s=importlib.util.spec_from_file_location('p189',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def rows(n=1000):
 t=datetime.datetime(2021,11,1,tzinfo=datetime.timezone.utc);b=[];e=[]
 for i in range(n):
  z=t+datetime.timedelta(hours=i);bc=100*(1.0002**i);ec=50*(1.00025**i);bq=1e7*(1+0.2*((i%19)+1));eq=8e6*(1+0.25*((i%17)+1))
  b.append((z,bc,bc,bc,bc,bq));e.append((z,ec,ec,ec,ec,eq))
 return b,e
def test_signal_is_strict_t_minus_1_for_price_and_volume():
 b,e=rows();base=m.signal_series(b,e);idx=m.N+20;b2=list(b);e2=list(e)
 b2[idx]=(b2[idx][0],b2[idx][1],b2[idx][2],b2[idx][3],b2[idx][4]*9,b2[idx][5]*99);e2[idx]=(e2[idx][0],e2[idx][1],e2[idx][2],e2[idx][3],e2[idx][4]*7,e2[idx][5]*77)
 alt=m.signal_series(b2,e2);k=next(i for i,x in enumerate(base) if x[0]==b[idx][0]);assert base[k][1:4]==alt[k][1:4]
def test_market_neutral_and_frozen_constants():
 b,e=rows();ss=m.signal_series(b,e);assert m.N==168 and m.THRESH==2.0 and m.LEG==.10
 assert all(abs(pb+pe)<1e-15 and abs(pb)+abs(pe) in (0,.2) for _,pb,pe,*_ in ss)
def test_cost_monotonicity():
 b,e=rows();a=m.evaluate(b,e,m.SEVERE);z=m.evaluate(b,e,m.SUPERSEVERE);assert z['return']<=a['return']+1e-12
def test_holdout_firewall_before_value_parse_and_native_field_required():
 with tempfile.TemporaryDirectory() as d:
  p=pathlib.Path(d)/'x.csv'
  with p.open('w',newline='') as f:
   w=csv.writer(f);w.writerow(['timestamp','open','high','low','close','quote_volume']);w.writerow(['2024-01-17T23:00:00Z',1,1,1,1,10]);w.writerow(['2024-01-18T00:00:00Z','BAD','BAD','BAD','BAD','BAD'])
  r,h=m.load_train(p);assert len(r)==1 and r[0][5]==10
  q=pathlib.Path(d)/'bad.csv';q.write_text('timestamp,open,high,low,close,volume\n2024-01-17T23:00:00Z,1,1,1,1,10\n')
  try:m.load_train(q);assert False
  except ValueError as x:assert 'quote_volume' in str(x)
def test_deterministic():
 b,e=rows();assert m.signal_series(b,e)==m.signal_series(b,e)
