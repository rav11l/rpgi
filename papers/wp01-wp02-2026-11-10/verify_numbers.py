from pathlib import Path
import sys, csv, json, hashlib, io, contextlib, runpy, statistics as st
import numpy as np

ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path('D:/Claude Chats/Real Estate Kazan')
REPO=ROOT/'RPGI/rpgi'
OUT=Path(__file__).parent
sys.path.insert(0,str(REPO/'code'))
from rosstat_parse import parse, edition_rank
from rosstat_gap import qv

books={}
for f in (REPO/'data/sources/rosstat').glob('*.xlsx'):
    b=parse(f)
    if not b or not b['market']: continue
    key=(b['year'],b['market'])
    if key not in books or edition_rank(b['path'])<edition_rank(books[key]['path']): books[key]=b
panel={}
for year in range(2021,2027):
    p,v=books[(year,'perv')],books[(year,'vtor')]
    for reg in p['data'].keys() & v['data'].keys():
        vals=[qv(p['data'][reg],q) for q in ['I','II']]+[qv(v['data'][reg],q) for q in ['I','II']]
        if None not in vals and all(x>0 for x in vals): panel[year,reg]=(sum(vals[:2])/sum(vals[2:])-1)*100
stored=list(csv.DictReader((REPO/'data/rosstat_centres_gap_2021_2026.csv').open(encoding='utf-8-sig'),delimiter=';'))
errors=[abs(panel[int(r['year']),r['centre']]-float(r['gap_pct'])) for r in stored]
with contextlib.redirect_stdout(io.StringIO()):
    c=runpy.run_path(str(REPO/'code/counts_check.py'))
    f=runpy.run_path(str(REPO/'code/fe_panel.py'))
    rates=runpy.run_path(str(REPO/'code/rates_check.py'))
tat=c['TAT']; years=list(range(2021,2027)); gaps=[panel[y,tat] for y in years]
corr=lambda a,b:float(np.corrcoef(a,b)[0,1])
summary=[]
for y in years:
    vals=sorted([g for (yy,r),g in panel.items() if yy==y],reverse=True)
    g=panel[y,tat]; med=st.median(vals)
    summary.append(dict(year=y,gap=g,median=med,rank=vals.index(g)+1,n=len(vals),ratio=g/med))
windows={}
for label,months in [('available',None),('H1',c['H1'])]:
    a=[c['agg'](tat,y,months) for y in years]
    vol=[100*x[1]/x[0] for x in a]; num=[100*x[3]/x[2] for x in a]
    windows[label]=dict(volume_share=vol,count_share=num,r_vol=corr(gaps,vol),rd_vol=corr(np.diff(gaps),np.diff(vol)),r_count=corr(gaps,num),rd_count=corr(np.diff(gaps),np.diff(num)),loo_levels=[corr(gaps[:i]+gaps[i+1:],vol[:i]+vol[i+1:]) for i in range(6)],r_diff_without_2026=corr(np.diff(gaps)[:-1],np.diff(vol)[:-1]))
p=f['panel']; regs=sorted(set(x[0] for x in p)); yy=sorted(set(x[1] for x in p))
dummy=np.array([[1]+[int(r==rr) for rr in regs[1:]]+[int(y==zz) for zz in yy[1:]] for r,y,g,s in p],dtype=float)
G=np.array([r[2] for r in p]); S=np.array([r[3] for r in p])
Gres=G-dummy@np.linalg.lstsq(dummy,G,rcond=None)[0]; Sres=S-dummy@np.linalg.lstsq(dummy,S,rcond=None)[0]
X=np.column_stack([S,dummy]); beta=np.linalg.lstsq(X,G,rcond=None)[0]; resid=G-X@beta
inv=np.linalg.inv(X.T@X); meat=np.zeros((X.shape[1],X.shape[1]))
for reg in regs:
    mask=np.array([r[0]==reg for r in p]); z=X[mask].T@resid[mask]; meat+=np.outer(z,z)
cov=inv@meat@inv*(len(regs)/(len(regs)-1))*((len(p)-1)/(len(p)-X.shape[1])); se=float(np.sqrt(cov[0,0])); assert len(regs)==73; cv=1.99346356627858 # t_0.975, 72 degrees of freedom
cross=[(panel[2025,reg],f['share_year'](reg,2025)) for reg in regs if (2025,reg) in panel and f['share_year'](reg,2025)]
fe=dict(n=len(p),regions=len(regs),pooled_r=corr(G,S),exact_fe_r=corr(Gres,Sres),slope=float(beta[0]),cluster_se=se,ci95=[float(beta[0]-cv*se),float(beta[0]+cv*se)],cross2025_n=len(cross),cross2025_r=corr([x[0] for x in cross],[x[1] for x in cross]))
def share(reg,month,count=False):
    mt,dt,md,dd=(c['mNt'],c['dNt'],c['mNd'],c['dNd']) if count else (c['mVt'],c['dVt'],c['mVd'],c['dVd'])
    return 100*float(dd[reg][md.index(month)])/float(dt[reg][mt.index(month)])
rf='РОССИЙСКАЯ ФЕДЕРАЦИЯ'
febrows=list(csv.DictReader((REPO/'data/cbr_ddu_share_regions_2026_02.csv').open(encoding='utf-8-sig')))
deltas=[share(r['регион'],'Февраль 2026')-share(r['регион'],'Январь 2026') for r in febrows]
feb=dict(n=len(deltas),fall=sum(x<0 for x in deltas),median=st.median(deltas),min=min(deltas),max=max(deltas),regions={reg:dict(volume=[share(reg,mm) for mm in ['Январь 2026','Февраль 2026']],count=[share(reg,mm,True) for mm in ['Январь 2026','Февраль 2026']]) for reg in [rf,tat]},seasonal_steps=[share(rf,f'Февраль {y}')-share(rf,f'Январь {y}') for y in range(2019,2026)])
rateout={}
for label,months in [('available',list(range(1,13))),('H1',list(range(1,7)))]:
    A=rates['annual'](months); spread=[A[y][2]-A[y][1] for y in years]
    rateout[label]=dict(r=corr(gaps,spread),rd=corr(np.diff(gaps),np.diff(spread)))
src=ROOT/'Журнал проверки данных/matrix_land_openness_2026-09-11.csv'
matrix=list(csv.DictReader(src.open(encoding='utf-8-sig'),delimiter=';')); fields=list(matrix[0])[1:-1]
def totals(rows): return {v:sum(r[k]==v for r in rows for k in fields) for v in sorted({r[k] for r in rows for k in fields})}
before=totals(matrix)
for r in matrix:
    if r['город']=='Санкт-Петербург':
        r['Цена начальная']=r['Цена итоговая']='частично'
        r['Перечень решений']='не проверено' # a general law is not a register of individual decisions
    for k in fields:
        if r[k]=='не публикуется': r[k]='не найдено'
    r['сумма_баллов']=str(sum({'раскрыто':2,'частично':1}.get(r[k],0) for k in fields))
matrix.sort(key=lambda r:-int(r['сумма_баллов']))
with (OUT/'matrix-reviewed.csv').open('w',encoding='utf-8-sig',newline='') as fh:
    writer=csv.DictWriter(fh,fieldnames=list(matrix[0]),delimiter=';'); writer.writeheader();writer.writerows(matrix)
available_months=[m for m in c['mVt'] if m.endswith('2026') and m in c['mVd'] and m in c['mNt'] and m in c['mNd']]
result=dict(source_rows=len(panel),max_gap_rounding_error=max(errors),available_months_2026=available_months,summary=summary,windows=windows,fe=fe,feb=feb,rates=rateout,matrix_original=before,matrix_reviewed=totals(matrix))
(OUT/'verified-numbers.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [*list((REPO/'data/sources/rosstat').glob('*.xlsx')),*list((REPO/'data/sources/cbr').glob('*.xlsx')),src]}
(OUT/'source-hashes.json').write_text(json.dumps(hashes,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=True,indent=2))
