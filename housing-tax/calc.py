# Расчёты к WP-2026-07 «Налог на непроданные квартиры в Татарстане».
# Запуск из корня репозитория или из каталога housing-tax: python housing-tax/calc.py
# Входные данные — файлы каталога escrow (те же, что в WP-2026-05).
import pandas as pd, numpy as np, json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ESCROW=HERE.parent/'escrow'
OUT=HERE/'calc_results.json'
src=ESCROW/'sources'/'eisgs'/'eisgs_kazan_objects.csv'
o=pd.read_csv(src,encoding='utf-8-sig')
o['ready']=pd.to_datetime(o.objReady100PercDt,errors='coerce')
o['yr']=o.ready.dt.year
o['unsold_sq']=o.sqLiving*(1-o.soldOutPercent)
R={}
c=o[(o.siteStatus=='Сданные')&o.soldOutPercent.notna()&(o.yr>=2023)]
g=c.groupby('yr').agg(n=('objId','size'),sq=('sqLiving','sum'),unsold=('unsold_sq','sum'))
g['share']=g.unsold/g.sq
R['completed']=g.round(3).reset_index().to_dict('records')
R['completed_total']=dict(n=int(len(c)),sq=float(c.sqLiving.sum()),unsold=float(c.unsold_sq.sum()),
  share=float(c.unsold_sq.sum()/c.sqLiving.sum()),
  obj_unsold_median=float(c.unsold_sq.median()),obj_unsold_p90=float(c.unsold_sq.quantile(.9)),
  obj_share_median=float((1-c.soldOutPercent).median()))
s=o[o.siteStatus=='Строящиеся'].copy()
s['pyr']=pd.to_datetime(s.objReady100PercDt,errors='coerce').dt.year
gs=s.groupby('pyr').agg(n=('objId','size'),sq=('sqLiving','sum'),unsold=('unsold_sq','sum'))
gs['share']=gs.unsold/gs.sq
R['building']=gs.round(3).reset_index().to_dict('records')
# economics
K=122000; P=234000
R['per_m2']={'2027':K*0.01,'2028':K*0.02,'pct_price_2027':K*0.01/P,'pct_price_2028':K*0.02/P,
 'flat50_2027':50*K*0.01,'flat50_2028':50*K*0.02,'carry_13pct':0.13*P,'tax_to_carry_2027':K*0.01/(0.13*P),'tax_to_carry_2028':K*0.02/(0.13*P)}
# per-object tax 2028 (completed objects, upper bound: snapshot)
c=c.assign(tax28=c.unsold_sq*K*0.02)
R['obj_tax28']=dict(median=float(c.tax28.median()),p90=float(c.tax28.quantile(.9)),max=float(c.tax28.max()),total=float(c.tax28.sum()))
# RT scenarios (stock in mln m2 at average for the year)
# stock = annual inflow x average remaining exposure
inflow=1.0*0.22   # mln m2/yr: commercial MKD ~1.0 mln m2 x 22% unsold at completion (EISGS Kazan 2023-26)
sc={'низкий':round(inflow*1.0,2),'базовый':round(inflow*1.8,1),'высокий':0.80}  # high: BO 1 bn at 1% / 122k
R['rt']={k:{'stock':v,'2027':v*1e6*K*0.01/1e9,'2028':v*1e6*K*0.02/1e9} for k,v in sc.items()}
R['rt_sens_K']={k:{'K100':v*1e6*100000*0.02/1e9,'K140':v*1e6*140000*0.02/1e9} for k,v in sc.items()}
# model project from report: 50k m2, price 210k, revenue 10.5 bn, profit 3.30 base / 1.48 crisis
proj=[]
for u in [0.17,0.28,0.46]:
  for T in [1,2,3]:
    ay=u*50000*T/2  # linear sell-down over T years
    t27=ay*K*0.01; t28=ay*K*0.02
    proj.append(dict(u=u,T=T,area_years=ay,tax28_mln=t28/1e6,pct_rev=t28/10.5e9,pct_profit_base=t28/3.30e9,pct_profit_crisis=t28/1.48e9,after_profit_tax_mln=t28*0.75/1e6))
R['project']=proj
# max rational discount ≈ tax per year × expected remaining exposure
R['discount_bound']={T:{'rub':K*0.02*T,'pct':K*0.02*T/P} for T in [1,2,3]}
# CBR coverage RT
d=pd.read_csv(ESCROW/'cbr_pf_regions.csv',parse_dates=['date'])
t=d[d.region.str.contains('Татарстан')].sort_values('date')
R['cbr']=t[['date','debt','escrow','cov']].dropna().iloc[[0,-1]].assign(date=lambda x:x.date.dt.strftime('%Y-%m-%d')).round(3).to_dict('records')
json.dump(R,open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=1,default=float)
print(json.dumps(R,ensure_ascii=False,indent=1,default=float))

# ---- v1.1: six-month registration window (art.16 214-FZ as amended by 487-FZ) ----
d=0.5
def taxable_share(T): return (T-d)**2/T**2   # linear sell-down over T years
R['v11_project']=[dict(u=u,T=T,tax28_mln=u*50000*(T-d)**2/(2*T)*K*0.02/1e6) for u in [0.17,0.28,0.46] for T in [1,2,3]]
R['v11_rt']={}
for nm,m in [('низкий',1.0),('базовый',1.8)]:
    s=0.22*m*taxable_share(2*m)
    R['v11_rt'][nm]=dict(m=m,share=taxable_share(2*m),stock=s,y2027=s*1e6*K*0.01/1e9,y2028=s*1e6*K*0.02/1e9)
R['v11_rt']['высокий']=dict(stock=0.8,y2027=0.8e6*K*0.01/1e9,y2028=0.8e6*K*0.02/1e9,note='BO-based, window not applied')
json.dump(R,open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=1,default=float)
print(json.dumps(R['v11_rt'],ensure_ascii=False,indent=1,default=float))
