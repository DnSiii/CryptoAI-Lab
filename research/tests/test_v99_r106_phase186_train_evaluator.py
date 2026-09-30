import csv,datetime,importlib.util,pathlib,tempfile
P=pathlib.Path(__file__).parents[1]/'tools'/'v99_r106_phase186_train_evaluator.py';s=importlib.util.spec_from_file_location('p186',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def rows(n=1000):
 t=datetime.datetime(2021,11,1,tzinfo=datetime.timezone.utc);b=[];e=[]
 for i in range(n):
  x=100*(1.001**i)*(1+0.01*((i%19)-9)/9);y=50*(1.0011**i)*(1+0.012*((i%17)-8)/8)
  z=t+datetime.timedelta(hours=i); b.append((z,x,x,x,x,1));e.append((z,y,y,y,y,1))
 return b,e
def test_signal_is_t_minus_1_causal():
 b,e=rows();base=m.signal_series(b,e);idx=m.N+20
 # Mutating contemporaneous close(t) must not change the signal/positions stamped t.
 b2=list(b);e2=list(e);tb=idx;b2[tb]=(b2[tb][0],*b2[tb][1:4],b2[tb][4]*9,b2[tb][5]);e2[tb]=(e2[tb][0],*e2[tb][1:4],e2[tb][4]*7,e2[tb][5])
 alt=m.signal_series(b2,e2);k=next(i for i,x in enumerate(base) if x[0]==b[idx][0]);assert base[k][1:5]==alt[k][1:5]
def test_market_neutral_and_frozen_constants():
 b,e=rows();s=m.signal_series(b,e);assert m.N==168 and m.THRESH==2.0 and m.LEG==.10
 assert all(abs(pb+pe)<1e-15 and abs(pb)+abs(pe) in (0,.2) for _,pb,pe,*_ in s)
def test_cost_monotonicity():
 b,e=rows();a=m.evaluate(b,e,m.SEVERE);z=m.evaluate(b,e,m.SUPERSEVERE);assert z['return']<=a['return']+1e-12
def test_holdout_firewall_stops_before_value_parse():
 with tempfile.TemporaryDirectory() as d:
  p=pathlib.Path(d)/'x.csv'
  with p.open('w',newline='') as f:
   w=csv.writer(f);w.writerow(['timestamp','open','high','low','close','volume']);w.writerow(['2024-01-17T23:00:00Z',1,1,1,1,1]);w.writerow(['2024-01-18T00:00:00Z','BAD','BAD','BAD','BAD','BAD'])
  r,h=m.load_train(p);assert len(r)==1 and r[0][4]==1
def test_deterministic():
 b,e=rows();assert m.signal_series(b,e)==m.signal_series(b,e)
