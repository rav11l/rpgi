import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))  # запуск из любой папки
import pandas as pd, numpy as np, re
U='../capitalization/'
c=pd.read_csv('cbr_pf_regions.csv',parse_dates=['date'])
norm=lambda s: re.sub(r'[^а-яё ]','',s.lower().replace('ё','е')).replace('  ',' ').strip()
c['rk']=c.region.map(norm)
p=pd.read_csv(U+'panel_q.csv'); p['rk']=p.region.map(norm)
fix={'архангельская область без данных по ненецкому автономному округу':'архангельская область','в том числе ненецкий автономный округ':'ненецкий автономный округ','в том числе хантымансийский автономный округ югра':'хантымансийский автономный округ югра','в том числе ямалоненецкий автономный округ':'ямалоненецкий автономный округ','кемеровская область кузбасс':'кемеровская область','тюменская область без данных по хантымансийскому автономному округу югре и ямалоненецкому автономному округу':'тюменская область'}
p['rk']=p.rk.replace(fix)
miss=sorted(set(p.rk)-set(c.rk)); print('unmatched price regions:',miss)
# quarter-start snapshot: file dated first day of quarter's first month
c['year']=c.date.dt.year; c['m']=c.date.dt.month
qs=c[c.m.isin([1,4,7,10])].copy(); qs['q']=(qs.m-1)//3+1
qs=qs[['rk','year','q','debt','escrow','limit','cov','cov_lim','n_loans']]
d=p.merge(qs,on=['rk','year','q'],how='left')
d=d.sort_values(['rk','year','q'])
d['tq']=d.year.astype(str)+'Q'+d.q.astype(str)
for v in ['lp1','lp2','lgap']:
    d['d_'+v]=d.groupby('rk')[v].diff()
d['d_cov']=d.groupby('rk')['cov'].diff()
d['d_ldebt']=d.groupby('rk')['debt'].transform(lambda s: np.log(s.where(s>0)).diff())
d['d_lesc']=d.groupby('rk')['escrow'].transform(lambda s: np.log(s.where(s>0)).diff())
d['d_share_ddu']=d.groupby('rk')['share_ddu'].diff()
d.to_csv('cov_panel.csv',index=False)
s=d.dropna(subset=['cov','d_lp1'])
print('obs with cov & dlp1',len(s),'regions',s.rk.nunique(),'quarters',sorted(s.tq.unique()))
print(s['cov'].describe().round(3))
