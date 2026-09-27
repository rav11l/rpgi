import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))  # запуск из любой папки
import pandas as pd, numpy as np
o=pd.read_csv('sources/eisgs/eisgs_kazan_objects.csv',encoding='utf-8-sig',dtype={'rpdNum':str})
p=pd.read_csv('sources/eisgs/eisgs_kazan_pd_versions.csv',encoding='utf-8-sig')
p['d']=pd.to_datetime(p.rpdIssueDate,format='%d-%m-%Y',errors='coerce')
o['ready']=pd.to_datetime(o.objReady100PercDt,errors='coerce')
o['delay_m']=(o.diffY.fillna(0)*12+o.diffM.fillna(0)+o.diffD.fillna(0)/30.44).where(o.delayed==1,0.0)
# planned date: for completed = ready - delay; ongoing = verification readyDate
def planned(r):
    if r.objStatus==2:
        if r.delayed==1:
            return r.ready-pd.DateOffset(years=int(r.diffY),months=int(r.diffM),days=int(r.diffD))
        return r.ready
    return pd.to_datetime(r.v_readyDate,errors='coerce')
o['P']=o.apply(planned,axis=1)
NOW=pd.Timestamp('2026-09-26')
o['cut']=np.where(o.objStatus==2,o.P-pd.DateOffset(months=6),NOW)
o['cut']=pd.to_datetime(o['cut'])
pu=p.drop_duplicates(['objId','rpdIssueDate'])
g=pu.merge(o[['objId','cut']],on='objId')
first=pu.groupby('objId').d.min().rename('pd_first')
o=o.merge(first,on='objId',how='left')
w=g[g.d<=g.cut]
o=o.merge(w.groupby('objId').size().rename('pd_to_cut'),on='objId',how='left')
w12=g[(g.d<=g.cut)&(g.d>g.cut-pd.DateOffset(months=12))]
o=o.merge(w12.groupby('objId').size().rename('pd_12m'),on='objId',how='left')
o['months_obs']=((o.cut-o.pd_first).dt.days/30.44).clip(lower=1)
o['pd_rate']=o.pd_to_cut/o.months_obs
o['horizon_m']=((o.P-o.pd_first).dt.days/30.44)
o['houses_in_pd']=o.groupby('rpdNum').objId.transform('count')
o.to_csv('panel.csv',index=False)
print(o[['pd_to_cut','pd_12m','pd_rate','horizon_m','houses_in_pd']].describe().round(2).to_string())
