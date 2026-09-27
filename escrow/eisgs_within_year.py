import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))  # запуск из любой папки
import pandas as pd, numpy as np
from sklearn.metrics import roc_auc_score
g=pd.read_csv('projects.csv',parse_dates=['P','ready'])
g['pyr']=g.P.dt.year; g['ryr']=g.ready.dt.year
print(g.groupby('pyr').agg(n=('rpdNum','size'),dl=('delayed','sum'),d3=('d3','sum')))
o=pd.read_csv('panel.csv',parse_dates=['ready'])
done=o[(o.objStatus==2)]; print('completed 2019-2022 residential',((done.ready<'2023')&(done.flats>0)).sum(),'marks',((done.ready<'2023')&(done.delayed==1)).sum(), 'all completed <2023',(done.ready<'2023').sum())
print('ongoing',(o.objStatus==0).sum(),'residential',((o.objStatus==0)&(o.flats>0)).sum())
rng=np.random.default_rng(5)
def pw_auc(d,x,y,strat):
    num=den=0
    for _,s in d.groupby(strat):
        pos=s[s[y]==1][x].values; neg=s[s[y]==0][x].values
        for p in pos: num+=(p>neg).sum()+0.5*(p==neg).sum(); den+=len(neg)
    return num/den if den else np.nan, den
def boot(fn,d,B=1000):
    d=d.reset_index(drop=True); idx={k:v.values for k,v in d.groupby('devInn').groups.items()}; devs=list(idx); r=[]
    for _ in range(B):
        s=rng.choice(len(devs),len(devs)); ii=np.concatenate([idx[devs[k]] for k in s]); dd=d.iloc[ii]
        try:
            v=fn(dd)
            if v==v: r.append(v)
        except Exception: pass
    return np.percentile(r,[2.5,97.5])
for y in ['delayed','d3']:
    for yr in ['pyr','ryr']:
        f=lambda d: roc_auc_score(d[y],d.groupby(yr)[y].transform('mean')) if d[y].nunique()==2 else np.nan
        # year-only AUC: in-sample year shares (upper bound)
        print(y,yr,'year-only AUC',round(f(g),2),boot(f,g).round(2))
g['dev_loo']=g.groupby('devInn').delayed.transform(lambda s:(s.sum()-s)/(len(s)-1) if len(s)>1 else np.nan)
g['dev_loo3']=g.groupby('devInn').d3.transform(lambda s:(s.sum()-s)/(len(s)-1) if len(s)>1 else np.nan)
h=g.dropna(subset=['dev_loo']).copy()
for y,x in [('delayed','dev_loo'),('d3','dev_loo3')]:
    for st in ['pyr','ryr']:
        a,n=pw_auc(h,x,y,st); ci=boot(lambda d: pw_auc(d,x,y,st)[0],h)
        print('within',st,y,round(a,2),ci.round(2),'pairs',n)
    print('year-only on 63',y, round(roc_auc_score(h[y],h.groupby('pyr')[y].transform('mean')),2))
# project features within planned-year (pairwise) on 120
for x in ['pd_12m','pd_rate','horizon_m','log_flats']:
    for y in ['delayed','d3']:
        a,n=pw_auc(g.dropna(subset=[x]),x,y,'pyr'); ci=boot(lambda d: pw_auc(d.dropna(subset=[x]),x,y,'pyr')[0],g,500)
        print('within-pyr',x,y,round(a,2),ci.round(2),n)
# Сигнал застройщика: другие декларации того же года плановой даты против других лет
def other(r,same):
    m=(g.devInn==r.devInn)&(g.rpdNum!=r.rpdNum)&((g.pyr==r.pyr) if same else (g.pyr!=r.pyr))
    return g[m].delayed.mean() if m.any() else np.nan
for same in [True,False]:
    xx=g.apply(lambda r: other(r,same),axis=1); dd0=g.assign(x=xx).dropna(subset=['x']).reset_index(drop=True)
    a=roc_auc_score(dd0.delayed,dd0.x); rng2=np.random.default_rng(3)
    idx2={k:np.flatnonzero(dd0.devInn.values==k) for k in dd0.devInn.unique()}; dv=list(idx2); bs=[]
    for _ in range(1000):
        s=rng2.choice(len(dv),len(dv)); dd=dd0.iloc[np.concatenate([idx2[dv[k]] for k in s])]
        if dd.delayed.nunique()==2: bs.append(roc_auc_score(dd.delayed,dd.x))
    print('same-year' if same else 'other-year', round(a,2), np.percentile(bs,[2.5,97.5]).round(2), 'n',len(dd0),'pos',int(dd0.delayed.sum()))
