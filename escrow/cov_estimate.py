import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))  # запуск из любой папки
import pandas as pd, numpy as np
from linearmodels.panel import PanelOLS
d=pd.read_csv('cov_panel.csv')
d['unc']=(1-d['cov']).clip(lower=0)          # uncovered share (0 if fully covered)
d['low']=(d['cov']<1).astype(float)
d['l_dlp1']=d.groupby('rk').d_lp1.shift()
d['t']=d.year*4+d.q
def run(df,y,xs,label):
    s=df.dropna(subset=[y]+xs).set_index(['rk','t'])
    m=PanelOLS(s[y],s[xs],entity_effects=True,time_effects=True).fit(cov_type='clustered',cluster_entity=True)
    out=[f'{label:34s} y={y:7s} N={int(m.nobs)} R={s.index.get_level_values(0).nunique()}']
    for x in xs: out.append(f'   {x:12s} b={m.params[x]: .4f} se={m.std_errors[x]:.4f} t={m.tstats[x]: .2f}')
    print('\n'.join(out))
S=d[d.year*4+d.q>=2025*4+1]
for y in ['d_lp1','d_lgap','d_lp2']:
    run(S,y,['unc'],'A. uncovered share (start of q)')
for y in ['d_lp1','d_lgap']:
    run(S,y,['unc','d_share_ddu','l_dlp1'],'B. + controls')
    run(S,y,['cov'],'C. coverage level (linear)')
    run(S,y,['d_ldebt','d_lesc'],'D. debt vs escrow growth (prev q)')
# long panel with escrow/limit
L=d[d.year>=2022].copy()
L['l_covlim']=L['cov_lim'].replace([np.inf,-np.inf],np.nan)
for y in ['d_lp1','d_lgap','d_lp2']:
    run(L,y,['l_covlim'],'E. escrow/limit 2022-2026')
for y in ['lp1','lgap','lp2']:
    run(S,y,['unc'],'F. LEVEL on uncovered share')
# model threshold: power check - MDE
print(S[['unc','cov']].describe().round(3).to_string())
print('share region-quarters with cov<1:', (S['cov']<1).mean().round(3))
