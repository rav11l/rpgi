# -*- coding: utf-8 -*-
"""Если связь 0,89 — арифметический артефакт рублёвой доли, она должна быть
универсальной: цена первички стоит и в числителе доли, и в разрыве у КАЖДОГО
региона. Проверяем распределение внутрирегиональных корреляций."""
import csv, io, statistics as st
import openpyxl

import os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(BASE, "data") + os.sep
gaps = {}
for r in csv.DictReader(io.open(D+"rosstat_centres_gap_2021_2026.csv", encoding="utf-8"), delimiter=";"):
    gaps.setdefault(r["centre"], {})[int(r["year"])] = float(r["gap_pct"])

def load(fn):
    ws = openpyxl.load_workbook(D+"sources/cbr/"+fn, read_only=True, data_only=True)["в рублях"]
    rows = [list(x) for x in ws.iter_rows(values_only=True)]
    h = next(i for i, r in enumerate(rows) if r and isinstance(r[1], str) and "Январь 2019" in str(r[1]))
    return [str(x).strip() if x else "" for x in rows[h]], {str(r[0]).strip(): r for r in rows[h+1:] if r and r[0]}
mt, dt = load("02_11_New_loans_mortgage.xlsx")
md, dd = load("02_16_New_loans_scpa_mortgage.xlsx")

def share_year(reg, year):
    tot = ddu = 0
    for i, mm in enumerate(mt):
        if not mm or not mm.endswith(str(year)) or mm not in md: continue
        j = md.index(mm)
        try: t, d = float(dt[reg][i]), float(dd[reg][j])
        except: continue
        tot += t; ddu += d
    return 100*ddu/tot if tot else None

def corr(a, b):
    n = len(a)
    if n < 4: return None
    ma, mb = sum(a)/n, sum(b)/n
    va = sum((x-ma)**2 for x in a); vb = sum((y-mb)**2 for y in b)
    if va == 0 or vb == 0: return None
    return sum((x-ma)*(y-mb) for x, y in zip(a, b)) / ((va**.5)*(vb**.5))

res = []
for reg, d in gaps.items():
    if reg not in dt or reg not in dd: continue
    ys = sorted(y for y in d)
    g, s = [], []
    for y in ys:
        sh = share_year(reg, y)
        if sh: g.append(d[y]); s.append(sh)
    if len(g) >= 5:
        c = corr(g, s)
        if c is not None: res.append((c, reg, len(g)))

res.sort()
vals = [c for c, _, _ in res]
tat = [x for x in res if "Татарстан" in x[1]][0]
print(f"регионов с рядом >=5 лет: {len(res)}")
print(f"медиана внутрирегиональной корреляции: {st.median(vals):+.3f}")
print(f"среднее: {sum(vals)/len(vals):+.3f}   | стандартное отклонение: {st.pstdev(vals):.3f}")
q = st.quantiles(vals, n=4)
print(f"квартили: {q[0]:+.3f} / {q[1]:+.3f} / {q[2]:+.3f}")
print(f"доля регионов с r > 0: {100*sum(1 for v in vals if v>0)/len(vals):.0f} %")
print(f"доля регионов с r > 0,8: {100*sum(1 for v in vals if v>0.8)/len(vals):.0f} %  (их {sum(1 for v in vals if v>0.8)})")
rank = sum(1 for v in vals if v > tat[0]) + 1
print(f"\nТатарстан: r = {tat[0]:+.3f}, место {rank} из {len(res)} по величине связи")
print(f"верхние 5: {[(round(c,2), n.split('(')[0].strip()[:24]) for c,n,_ in res[-5:][::-1]]}")
print(f"нижние 5:  {[(round(c,2), n.split('(')[0].strip()[:24]) for c,n,_ in res[:5]]}")
