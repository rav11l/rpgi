# -*- coding: utf-8 -*-
"""Доля выдач под ДДУ по ЧИСЛУ ДОГОВОРОВ вместо объёма в рублях.
Проверяет, не является ли связь разрыва и доли арифметическим артефактом:
в рублёвой доле цена первички стоит в числителе, и в разрыве она же."""
import csv, io, statistics as st
import openpyxl

import os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(BASE, "data") + os.sep
S = D + "sources/cbr/"
TAT = "Республика Татарстан (Татарстан)"

gaps = {}
for r in csv.DictReader(io.open(D+"rosstat_centres_gap_2021_2026.csv", encoding="utf-8"), delimiter=";"):
    gaps.setdefault(r["centre"], {})[int(r["year"])] = float(r["gap_pct"])

def load(fn):
    ws = openpyxl.load_workbook(S+fn, read_only=True, data_only=True)["в рублях"]
    rows = [list(x) for x in ws.iter_rows(values_only=True)]
    h = next(i for i, r in enumerate(rows) if r and len(r) > 1 and isinstance(r[1], str) and "Январь 2019" in str(r[1]))
    return [str(x).strip() if x else "" for x in rows[h]], {str(r[0]).strip(): r for r in rows[h+1:] if r and r[0]}

mVt, dVt = load("02_11_New_loans_mortgage.xlsx")        # объём всего, млн руб.
mVd, dVd = load("02_16_New_loans_scpa_mortgage.xlsx")   # объём ДДУ
mNt, dNt = load("02_10_Quantity_mortgage.xlsx")         # количество всего
mNd, dNd = load("02_15_Quantity_scpa_mortgage.xlsx")    # количество ДДУ

MONTHS = ["Январь","Февраль","Март","Апрель","Май","Июнь","Июль","Август","Сентябрь","Октябрь","Ноябрь","Декабрь"]

def agg(reg, year, months=None):
    """суммы за год (или за окно месяцев): объём всего/ДДУ, число всего/ДДУ"""
    out = [0.0, 0.0, 0.0, 0.0]
    for i, mm in enumerate(mVt):
        if not mm or not mm.endswith(str(year)): continue
        if months and mm.split()[0] not in months: continue
        try:
            vt = float(dVt[reg][i])
            vd = float(dVd[reg][mVd.index(mm)]) if mm in mVd else None
            nt = float(dNt[reg][mNt.index(mm)]) if mm in mNt else None
            nd = float(dNd[reg][mNd.index(mm)]) if mm in mNd else None
            if None in (vd, nt, nd): continue
            out[0] += vt; out[1] += vd; out[2] += nt; out[3] += nd
        except: continue
    return out if out[0] and out[2] else None

def corr(a, b):
    n = len(a)
    if n < 3: return None
    ma, mb = sum(a)/n, sum(b)/n
    va = sum((x-ma)**2 for x in a); vb = sum((y-mb)**2 for y in b)
    if va == 0 or vb == 0: return None
    return sum((x-ma)*(y-mb) for x, y in zip(a, b)) / ((va**.5)*(vb**.5))

def diffs(x): return [x[i+1]-x[i] for i in range(len(x)-1)]

H1 = MONTHS[:6]
print("=" * 74)
print("ТАТАРСТАН: доля по объёму против доли по числу договоров")
print("=" * 74)
for label, months in (("год целиком", None), ("I–II кварталы", H1)):
    years = sorted(gaps[TAT])
    g, sv, sn, cheque = [], [], [], []
    for y in years:
        a = agg(TAT, y, months)
        if not a: continue
        vt, vd, nt, nd = a
        g.append(gaps[TAT][y]); sv.append(100*vd/vt); sn.append(100*nd/nt)
        # превышение среднего кредита под ДДУ над средним по прочим
        vo, no = vt-vd, nt-nd
        cheque.append((vd/nd)/(vo/no) - 1 if nd and no else None)
    print(f"\n— окно: {label}")
    print("  год:           " + "  ".join(f"{y}" for y in years))
    print("  разрыв, %:     " + "  ".join(f"{x:5.1f}" for x in g))
    print("  доля ₽, %:     " + "  ".join(f"{x:5.1f}" for x in sv))
    print("  доля шт., %:   " + "  ".join(f"{x:5.1f}" for x in sn))
    print("  чек ДДУ/проч.: " + "  ".join(f"{x:+5.2f}" if x is not None else "    -" for x in cheque))
    print(f"  корреляция в уровнях:   по объёму {corr(g, sv):+.3f}   |   по числу договоров {corr(g, sn):+.3f}")
    print(f"  корреляция в разностях: по объёму {corr(diffs(g), diffs(sv)):+.3f}   |   по числу договоров {corr(diffs(g), diffs(sn)):+.3f}")

# ——— панель с фиксированными эффектами на долях по числу договоров ———
print("\n" + "=" * 74)
print("ПАНЕЛЬ: то же на долях по числу договоров")
print("=" * 74)
panel = []
for reg, d in gaps.items():
    if reg not in dVt or reg not in dNt: continue
    for y in range(2022, 2027):
        if y in d and (y-1) in d:
            a1, a0 = agg(reg, y), agg(reg, y-1)
            if not a1 or not a0: continue
            s1 = 100*a1[3]/a1[2]; s0 = 100*a0[3]/a0[2]
            panel.append((reg, y, d[y]-d[y-1], s1-s0))
print(f"наблюдений: {len(panel)}, регионов: {len(set(r for r,_,_,_ in panel))}")
print(f"объединённая корреляция разностей: {corr([x[3] for x in panel], [x[2] for x in panel]):+.3f}")
ym_g, ym_s = {}, {}
for reg, y, dg, ds in panel:
    ym_g.setdefault(y, []).append(dg); ym_s.setdefault(y, []).append(ds)
ym_g = {y: sum(v)/len(v) for y, v in ym_g.items()}; ym_s = {y: sum(v)/len(v) for y, v in ym_s.items()}
st1 = [(reg, dg-ym_g[y], ds-ym_s[y]) for reg, y, dg, ds in panel]
rm_g, rm_s = {}, {}
for reg, dg, ds in st1:
    rm_g.setdefault(reg, []).append(dg); rm_s.setdefault(reg, []).append(ds)
rm_g = {r: sum(v)/len(v) for r, v in rm_g.items()}; rm_s = {r: sum(v)/len(v) for r, v in rm_s.items()}
G = [dg-rm_g[reg] for reg, dg, ds in st1]; Sx = [ds-rm_s[reg] for reg, dg, ds in st1]
r_fe = corr(Sx, G); n = len(G)
print(f"двусторонние фиксированные эффекты: r = {r_fe:+.3f}, t ≈ {r_fe/((1-r_fe**2)/(n-2))**0.5:+.2f}")

# ——— февраль 2026 по числу договоров ———
print("\n" + "=" * 74)
print("ФЕВРАЛЬ 2026 по числу договоров (для проверки раздела колонки)")
print("=" * 74)
for reg, lbl in ((("РОССИЙСКАЯ ФЕДЕРАЦИЯ"), "Россия"), (TAT, "Татарстан")):
    for mm in ("Январь 2026", "Февраль 2026"):
        i, j = mNt.index(mm), mNd.index(mm)
        sh = 100*float(dNd[reg][j])/float(dNt[reg][i])
        iv, jv = mVt.index(mm), mVd.index(mm)
        shv = 100*float(dVd[reg][jv])/float(dVt[reg][iv])
        print(f"  {lbl:10s} {mm:14s} по числу {sh:5.1f} %   по объёму {shv:5.1f} %")
