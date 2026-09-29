import csv,importlib.util
from pathlib import Path
from datetime import datetime,timezone,timedelta
P=Path(__file__).parents[1]/'tools'/'v99_r106_phase183_train_evaluator.py';s=importlib.util.spec_from_file_location('p183',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def write(p,n=700,k=0):
 with open(p,'w',newline='') as f:
  w=csv.writer(f);w.writerow(['timestamp','open','high','low','close','volume']);t=datetime(2021,11,1,tzinfo=timezone.utc);px=100.
  for i in range(n):px*=1+.0003*((i%11)-5)+k;w.writerow([(t+timedelta(hours=i)).isoformat(),px,px*1.01,px*.99,px,100+i%13])
def test_determinism_firewall_and_cost(tmp_path):
 b=tmp_path/'b';e=tmp_path/'e';write(b);write(e,k=.00001);rb,_=m.load_train(b);re,_=m.load_train(e);a=m.evaluate(rb,re,m.SEVERE);assert a==m.evaluate(rb,re,m.SEVERE);z=m.evaluate(rb,re,m.SUPERSEVERE);assert z['return']<=a['return']+1e-12
 with open(b,'a') as f:f.write('2024-01-18T00:00:00+00:00,SECRET,SECRET,SECRET,SECRET,SECRET\n')
 rb2,_=m.load_train(b);assert rb2==rb
def test_t_minus_1_contemporaneous_mutation_cannot_change_signal(tmp_path):
 b=tmp_path/'b';e=tmp_path/'e';write(b,800);write(e,800,k=.00002);rb,_=m.load_train(b);re,_=m.load_train(e);base=m.signal_series(rb,re);cut=500;re2=list(re);x=list(re2[cut]);x[4]*=5;re2[cut]=tuple(x);mut=m.signal_series(rb,re2);target=re[cut][0]
 assert [(x[0],x[1],x[2],x[3]) for x in base if x[0]<=target]==[(x[0],x[1],x[2],x[3]) for x in mut if x[0]<=target]
def test_constants_are_preregistered():assert (m.N,m.THRESH,m.GROSS,m.SUPERSEVERE)==(168,2.0,.20,2*m.SEVERE)
