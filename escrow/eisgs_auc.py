import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))  # запуск из любой папки
import pandas as pd, numpy as np
from sklearn.metrics import roc_auc_score
c=pd.read_csv('sample_completed.csv',parse_dates=['ready','P','cut'])
c['unsold']=1-c.soldOutPercent
# one row per project declaration (rpdNum): earliest planned date
g=c.groupby('rpdNum').agg(devInn=('devInn','first'),devName=('devName','first'),n_obj=('objId','size'),flats=('flats','sum'),
  delayed=('delayed','max'),delay_m=('delay_m','max'),P=('P','min'),ready=('ready','max'),
  pd_12m=('pd_12m','median'),pd_rate=('pd_rate','median'),horizon_m=('horizon_m','median'),unsold=('unsold','median')).reset_index()
g['d3']=(g.delay_m>=3).astype(int); g['log_flats']=np.log(g.flats); g['yr']=g.ready.dt.year
print(g.groupby('yr').agg(n=('rpdNum','size'),delayed=('delayed','sum'),d3=('d3','sum')))
print('devs',g.devInn.nunique(),'projects',len(g))
rng=np.random.default_rng(11)
def auc_ci(d,x,y,B=2000):
    d=d[[x,y,'devInn']].dropna().reset_index(drop=True); a=roc_auc_score(d[y],d[x]); devs=d.devInn.unique(); bs=[]
    idx={k:np.flatnonzero(d.devInn.values==k) for k in devs}
    for _ in range(B):
        s=rng.choice(devs,len(devs)); dd=d.iloc[np.concatenate([idx[k] for k in s])]
        if dd[y].nunique()==2: bs.append(roc_auc_score(dd[y],dd[x]))
    lo,hi=np.percentile(bs,[2.5,97.5]); return a,lo,hi,len(d),int(d[y].sum())
out=[]
for smp,df in [('2025–2026',g[g.ready>='2025-01-01']),('2023–2026',g)]:
    df=df.copy(); df['dev_loo']=df.groupby('devInn').delayed.transform(lambda s:(s.sum()-s)/(len(s)-1) if len(s)>1 else np.nan)
    for y in ['delayed','d3']:
        for x in ['pd_12m','pd_rate','horizon_m','log_flats','unsold','dev_loo']:
            a,lo,hi,n,pos=auc_ci(df,x,y); out.append([smp,y,x,round(a,2),round(lo,2),round(hi,2),n,pos])
r=pd.DataFrame(out,columns=['sample','outcome','feature','auc','lo','hi','n','pos']); print(r.to_string()); r.to_csv('auc_results.csv',index=False)
g.to_csv('projects.csv',index=False)
