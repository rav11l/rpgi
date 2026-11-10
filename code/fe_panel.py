# -*- coding: utf-8 -*-
"""Правильная спецификация вместо объединённой корреляции.
Внутрирегиональная связь в уровнях может быть общим трендом; год-эффекты его снимают."""
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
    if n < 3: return None
    ma, mb = sum(a)/n, sum(b)/n
    va = sum((x-ma)**2 for x in a); vb = sum((y-mb)**2 for y in b)
    if va == 0 or vb == 0: return None
    return sum((x-ma)*(y-mb) for x, y in zip(a, b)) / ((va**.5)*(vb**.5))

# ——— панель первых разностей ———
panel = []   # (регион, год, Δразрыв, Δдоля)
for reg, d in gaps.items():
    if reg not in dt or reg not in dd: continue
    for y in range(2022, 2027):
        if y in d and (y-1) in d:
            s1, s0 = share_year(reg, y), share_year(reg, y-1)
            if s1 is not None and s0 is not None: panel.append((reg, y, d[y]-d[y-1], s1-s0))

print(f"панель первых разностей: {len(panel)} наблюдений, {len(set(r for r,_,_,_ in panel))} регионов\n")

# 1. объединённая (как в статье)
print(f"1. Объединённая корреляция разностей (без эффектов): r = {corr([x[3] for x in panel], [x[2] for x in panel]):+.3f}")

# 2. внутрирегиональные корреляции разностей
byreg = {}
for reg, y, dg, ds in panel: byreg.setdefault(reg, []).append((ds, dg))
wr = [(corr([a for a,_ in v], [b for _,b in v]), reg) for reg, v in byreg.items() if len(v) >= 4]
wr = [(c, r) for c, r in wr if c is not None]
vals = sorted(c for c, _ in wr)
print(f"2. Внутрирегиональные корреляции разностей ({len(wr)} регионов с >=4 переходами):")
print(f"   медиана {st.median(vals):+.3f}, среднее {sum(vals)/len(vals):+.3f}, доля положительных {100*sum(1 for v in vals if v>0)/len(vals):.0f} %")

# 3. Joint fixed effects and region-clustered inference (v0.9.0).
from panel_utils import fit_twfe
import json
result = fit_twfe(panel)
print(f"3. Joint region/year fixed effects, n = {result['n']}, regions = {result['regions']}:")
print(f"   b = {result['slope']:+.6f}; cluster SE = {result['cluster_se']:.6f}; 95% CI = {result['ci95']}")
print("   An interval containing zero is not proof of a zero effect or equivalence.")
result['source_scope'] = 'Current data/sources/cbr workbooks; all available months. WP-01 uses its separately frozen August 2026 snapshot.'
with open(D + 'fe_panel_results.json', 'w', encoding='utf-8') as out:
    json.dump(result, out, ensure_ascii=False, indent=2)

ymean_g = {}; ymean_s = {}
for reg, y, dg, ds in panel:
    ymean_g.setdefault(y, []).append(dg); ymean_s.setdefault(y, []).append(ds)
ymean_g = {y: sum(v)/len(v) for y, v in ymean_g.items()}
ymean_s = {y: sum(v)/len(v) for y, v in ymean_s.items()}

# 4. только год-эффекты (внутри года, между регионами)
Gy = [dg - ymean_g[y] for reg, y, dg, ds in panel]
Sy = [ds - ymean_s[y] for reg, y, dg, ds in panel]
print(f"4. Только год-эффекты (сравнение регионов внутри одного года): r = {corr(Sy, Gy):+.3f}")

# 5. Татарстан в этой системе координат
tat = [x for x in panel if "Татарстан" in x[0]]
print(f"\n5. Татарстан, переходы: " + ", ".join(f"{y}: Δразрыв {dg:+.1f} / Δдоля {ds:+.1f}" for _, y, dg, ds in tat))
