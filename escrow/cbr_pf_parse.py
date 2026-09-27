import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))  # запуск из любой папки
import openpyxl, glob, re, pandas as pd, os
def key(h):
    h=h.lower()
    if 'субъект' in h: return 'region'
    if h.startswith('кол-во действующих'): return 'n_loans'
    if h.startswith('сумма действующих'): return 'limit'
    if h.startswith('задолженность'): return 'debt'
    if h.startswith('остатки средств'): return 'escrow'
    if 'ставка' in h: return 'rate'
    if h.startswith('сумма средств, перечисленных'): return 'released'
    if 'имеющих остатки' in h: return 'n_escrow_bal'
    if h.startswith('кол-во счетов эскроу'): return 'n_escrow'
    if 'раскрытых' in h and h.startswith('кол-во'): return 'n_released'
    return None
num=lambda x: float(x) if x is not None and re.match(r'^-?[\d.]+(e-?\d+)?$',str(x).strip()) else None
rows=[]
for f in sorted(glob.glob('sources/cbr_pf/*.xlsx')):
    d=os.path.basename(f)[:8]; date=pd.Timestamp(f'{d[4:]}-{d[2:4]}-{d[:2]}')
    ws=openpyxl.load_workbook(f,data_only=True).worksheets[0]; cols=None
    for r in ws.iter_rows(values_only=True):
        r=list(r)
        if cols is None:
            if r[1] and 'Субъект' in str(r[1]): cols=[key(str(c)) if c is not None else None for c in r]
            continue
        if r[0] is None or not re.match(r'^\d+$',str(r[0]).strip()) or r[1] is None: continue
        rec={'date':date}
        for c,v in zip(cols,r):
            if c=='region': rec['region']=re.sub(r'\s+',' ',re.sub(r'[\d*]+$','',str(v).strip())).strip()
            elif c: rec[c]=num(v)
        rows.append(rec)
df=pd.DataFrame(rows); df['cov']=df.escrow/df.debt; df['cov_lim']=df.escrow/df.limit
df.to_csv('cbr_pf_regions.csv',index=False)
print(df.shape, df.region.nunique())
t=df[df.region.str.contains('Татарстан')].sort_values('date'); print(t[['date','limit','debt','escrow','cov','cov_lim','n_loans']].to_string())
