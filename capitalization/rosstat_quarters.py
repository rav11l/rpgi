import os as _os; _os.chdir(_os.path.dirname(_os.path.abspath(__file__)))  # запуск из любой папки
import sys, glob, os, re, csv, openpyxl
import os; HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "code"))
from rosstat_parse import parse
SRC=os.path.join(HERE, "..", "data", "sources", "rosstat")
recs={}
for p in sorted(glob.glob(SRC+"/*.xlsx")):
    d=parse(p)
    qs=list(next(iter(d['data'].values())).keys())
    print(os.path.basename(p), d['market'], d['year'], qs[:6], len(d['data']))
    for reg,vals in d['data'].items():
        reg=re.sub(r'\d\)$','',reg).strip()   # сноска вида «Костромская область1)»
        for q,v in vals.items():
            m=re.search(r'([IV]+)\s*квартал',q)
            if not m or v is None: continue
            qn={'I':1,'II':2,'III':3,'IV':4}[m.group(1)]
            key=(reg,d['year'],qn,d['market'])
            # prefer 4kv edition (latest revision) -> first seen for 4kv files; 2kv-2026 only for 2026
            recs.setdefault(key,v)
rows={}
for (reg,y,q,mk),v in recs.items():
    rows.setdefault((reg,y,q),{})[mk]=v
with open("prices_q.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["centre","year","q","perv","vtor"])
    for (reg,y,q),d in sorted(rows.items()):
        if 'perv' in d and 'vtor' in d and d['perv']>0 and d['vtor']>0:
            w.writerow([reg,y,q,d['perv'],d['vtor']])
