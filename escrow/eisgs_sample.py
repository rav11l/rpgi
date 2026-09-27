import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))  # запуск из любой папки
import pandas as pd, numpy as np
o=pd.read_csv('panel.csv',parse_dates=['ready','P','cut','pd_first'])
c=o[(o.objStatus==2)&(o.ready>='2023-01-01')&(o.flats>0)].copy()
c['yr']=c.ready.dt.year
print(c.groupby('yr').agg(n=('objId','size'),delayed=('delayed','sum'),d3=('delay_m',lambda s:(s>=3).sum()),d6=('delay_m',lambda s:(s>=6).sum())))
# developer track record: share delayed among developer's (devInn) other objects with P < this cut
c=c.sort_values('P')
def track(r):
    prev=c[(c.devInn==r.devInn)&(c.ready<r.cut)&(c.objId!=r.objId)]
    return (prev.delayed.mean() if len(prev) else np.nan), len(prev)
tr=c.apply(lambda r: pd.Series(track(r),index=['dev_prev_delay','dev_prev_n']),axis=1)
c=pd.concat([c,tr],axis=1)
c['dev_n']=c.groupby('devInn').objId.transform('count')
c['log_flats']=np.log(c.flats)
c.to_csv('sample_completed.csv',index=False)
print('sample_completed.csv:',len(c),'objects')
