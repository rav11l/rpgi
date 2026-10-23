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

# ---- v1.3: жилые помещения прочих организаций (не застройщиков) ----
# Проект переводит на кадастровую базу жильё всех организаций, а не только застройщиков.
# Региональных данных о жилье организаций в открытой статистике нет; оценка — сценарная.
# Росстат, «Жилищное хозяйство в России. 2025», табл. 2.2 и диагр. 2.3: на конец 2024 г.
# частный фонд — 94,7 % всего фонда, в т. ч. в собственности граждан — 92,7 %;
# остаток 2,0 % — собственность юридических лиц и нераспределённый фонд (с 2020 г. включён в частный).
RF_fund=4293.0                      # млн м², весь жилищный фонд РФ на конец 2024 г.
RF_share_noncit=0.947-0.927         # доля фонда вне собственности граждан внутри частного
RT_pop=4.0                          # млн чел., постоянное население РТ (округлённо)
RT_fund=RT_pop*RF_fund/146.1        # приближение: обеспеченность РТ = средней по РФ
R['v13_other']={'RF_share_noncit':RF_share_noncit,'RT_fund_approx':RT_fund,
  'RT_upper_stock':RT_fund*RF_share_noncit-R['v11_rt']['базовый']['stock']}
sc13={'низкий':0.25,'базовый':0.5,'высокий':1.0}   # % фонда РТ: 1/8, 1/4, 1/2 общероссийской доли 2,0 %
R['v13_other']['scen']={}
for nm,pct in sc13.items():
    st=RT_fund*pct/100
    R['v13_other']['scen'][nm]=dict(pct=pct,stock=st,y2027=st*1e6*K*0.01/1e9,y2028=st*1e6*K*0.02/1e9,
        y2028_K100=st*1e6*100000*0.02/1e9)
R['v13_total']={nm:dict(y2027=R['v11_rt'][nm]['y2027']+R['v13_other']['scen'][nm]['y2027'],
                       y2028=R['v11_rt'][nm]['y2028']+R['v13_other']['scen'][nm]['y2028']) for nm in sc13}
json.dump(R,open(OUT,'w'),ensure_ascii=False,indent=1,default=float)
print(json.dumps({k:R[k] for k in ['v13_other','v13_total']},ensure_ascii=False,indent=1,default=float))

# ---- v1.4: кадастровая стоимость новостроек, переоценка, содержание, большой остаток ----
# 1) Выборка НСПД (23.10.2026): 58 квартир в 21 доме, введённом в 2024–2026 гг. (дома найдены по координатам
#    объектов ЕИСЖС), файл nspd_newbuild_flats.csv: кадастровый номер, площадь, кадастровая стоимость.
# 2) Переоценка: тур ГКО ОКС 2026–2027 гг.; сценарий +25 % к измеренной медиане с 01.01.2028.
# 3) Содержание непроданных помещений застройщиком (п. 7 ч. 2 ст. 153 ЖК РФ): 720 руб./м² в год, без окна.
# 4) Большой остаток: 28,5 % к вводу (дома 2026 г.), распродажа до 4 лет.
P=234000; MAINT=720.0; CARRY=0.13*P; REV=1.25
fl=pd.read_csv(HERE/'nspd_newbuild_flats.csv',encoding='utf-8')
fl['k']=fl.cost/fl.area
fl['price']=fl.objId.map(o.set_index('objId').averagePrice)
bd=fl.groupby(['objId','addr']).agg(k=('k','median'),price=('price','first')).reset_index()
bd['ratio']=bd.k/bd.price
KN=round(float(bd.k.median()),-3); KR=round(KN*REV,-3)  # медиана по домам
R['v14_nspd']=dict(flats=int(len(fl)),buildings=int(len(bd)),objects=int(bd.objId.nunique()),
    k_median_flats=float(fl.k.median()),k_median_bldg=float(bd.k.median()),
    k_p10=float(bd.k.quantile(.1)),k_p90=float(bd.k.quantile(.9)),
    ratio_median=float(bd.ratio.median()),ratio_p10=float(bd.ratio.quantile(.1)),
    ratio_p90=float(bd.ratio.quantile(.9)),ratio_max=float(bd.ratio.max()),K_new=KN,K_reval=KR)
R['v14_per_m2']={nm:dict(K=k,tax2028=k*0.02,pct_price_2028=k*0.02/P,tax_plus_maint=k*0.02+MAINT,
    tax_share_of_carry=k*0.02/CARRY,flat50_tax2028=50*k*0.02,flat50_maint=50*MAINT)
    for nm,k in [('фонд',K),('новостройки',KN),('после переоценки',KR)]}
R['v14_obj_reval']={q:R['obj_tax28'][q]*KR/K for q in ['median','p90','max']}
def proj(u,T,k,d=0.5):
    tax=u*50000*(T-d)**2/(2*T)*k*0.02; mnt=u*50000*T/2*MAINT
    return dict(u=u,T=T,K=k,tax_mln=tax/1e6,maint_mln=mnt/1e6,total_mln=(tax+mnt)/1e6,
        pct_profit_base=(tax+mnt)/3.30e9,pct_profit_crisis=(tax+mnt)/1.48e9,tax_only_crisis=tax/1.48e9)
R['v14_project']=[proj(u,T,k) for u in [0.17,0.285,0.46] for T in [2,3,4] for k in [KN,KR]]
disc=0.20*0.46*10.5e9; tl=proj(0.46,3,KR)
R['v14_tail']=dict(tl,discount20_mln=disc/1e6,pct_profit_base_after_disc=tl['total_mln']*1e6/(3.30e9-disc))
def rt(share,m,k):
    s=share*m*((2*m-0.5)/(2*m))**2
    return dict(share=share,m=m,taxable=s,y2028=s*1e6*k*0.02/1e9)
R['v14_rt']={'базовый':{'новостройки':rt(0.22,1.8,KN),'после переоценки':rt(0.22,1.8,KR)},
    'большой остаток':{'новостройки':rt(0.285,2.5,KN),'после переоценки':rt(0.285,2.5,KR)}}
json.dump(R,open(OUT,'w'),ensure_ascii=False,indent=1,default=float)
print(json.dumps({k:R[k] for k in ['v14_nspd','v14_per_m2','v14_obj_reval','v14_tail','v14_rt']},ensure_ascii=False,indent=1,default=float))
